import holoviews as hv
from holoviews import dim, opts, streams
from holoviews.selection import link_selections
import hvplot.pandas
import pandas as pd
from itertools import combinations
import numpy as np
from tqdm import trange, tqdm
import re
import panel as pn
import spatialpandas
import os
from bokeh.models import HoverTool
from classy import Class
import matplotlib.pyplot as plt
import copy
from multiprocessing import Pool

hv.extension('bokeh')
pn.extension()

# read in the .paramnames file and put it into list format
def load_params(filename):
    params_list = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            params = re.split(' \t ', line)
            params_list.append(params)
    return [item[0] for item in params_list], [item[1] for item in params_list]


# create a DataFrame with the chain files as rows and use a list of parameters as the column names
def load_data(filename, column_names):
    data = np.loadtxt(filename)
    df = pd.DataFrame(data[:,1:], columns=column_names)
    return df


def run_class(selection):
    # run class on the user's selection
    cosmo = Class()
    cosmo.set(selection)
    cosmo.set({'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'})
    cosmo.compute()

    # set variables for matter power spectrum and lensed CMB angular power spectra
    kk = np.logspace(-4,np.log10(3),1000)
    Pk = []
    h = cosmo.h()
    for k in kk:
        Pk.append(cosmo.pk(k*h,0.)*h**3)
    Pk = np.array(Pk)
    l = np.array(range(2,2501))
    factor = l*(l+1)/(2*np.pi)
    lensed_cl = cosmo.lensed_cl(2500)
    
    results = {'k': kk, 'Pk': Pk, 'l': l, 'Cl_tt': factor*lensed_cl['tt'][2:], 'Cl_ee': factor*lensed_cl['ee'][2:]}
    
    cosmo.struct_cleanup()
    cosmo.empty()
    return results


def compute_residuals(index, sample, sample_CDM):
    selection = sample.iloc[[index]].to_dict('index')
    selection_CDM = sample_CDM.iloc[[index]].to_dict('index')
    if __name__ == '__main__':
        with Pool() as p:
            [mycosmo, LambdaCDM] = p.map(run_class, [selection[index], selection_CDM[index]])
    else:
        mycosmo = run_class(selection[index])
        LambdaCDM = run_class(selection_CDM[index])

    pk_residuals = (mycosmo['Pk'] - LambdaCDM['Pk'])/LambdaCDM['Pk']*100
    cl_tt_residuals = (mycosmo['Cl_tt'] - LambdaCDM['Cl_tt'])/LambdaCDM['Cl_tt']*100
    cl_ee_residuals = (mycosmo['Cl_ee'] - LambdaCDM['Cl_ee'])/LambdaCDM['Cl_ee']*100
    
    residuals = {'pk_residuals': {'k': mycosmo['k'], 'Pk': pk_residuals}, 
                 'cl_tt_residuals': {'l': mycosmo['l'], 'Cl_TT': cl_tt_residuals}, 
                 'cl_ee_residuals': {'l': mycosmo['l'], 'Cl_EE': cl_ee_residuals}}
    return residuals


# generate a scatter plot using the key dimensions from a holoviews.Dataset object, with the CLASS output displayed alongside it
def viz(data, myfunction, myfunction_args, show_observables=True, latex_dict=None):
    # handle default case of no latex paramname dictionary
    if latex_dict is None:
        latex_dict = dict()
    # setting Panel widgets for user interaction
    variables = data.columns.values.tolist()
    var1 = pn.widgets.Select(value=variables[1], name='Horizontal Axis', options=variables)
    var2 = pn.widgets.Select(value=variables[2], name='Vertical Axis', options=variables)
    cmap_var = pn.widgets.Select(value=variables[0], name='Colormapped Parameter', options=variables)
    cmap_option = pn.widgets.Checkbox(value=True, name='Show Colormap', align='end')
    
    #  given a param name, find corresponding latex-formatted param name
    def lookup_latex_label(param):
        try:
            latex_param = latex_dict[param]
            label = r'$${}$$'.format(latex_param)
            return label
        except KeyError:
            label = param
            return label
    
    # function for generating the scatter plot, given 2 dimensions as x and y axes, and an additional dimension to colormap
    # to the points on the plot. Also has an option to show or hide the colormap
    def plot_data(kdim1, kdim2, colordim, showcmap):
        if showcmap == True:
            cmapping = opts.Points(color=dim(colordim),
                colorbar=True,
                cmap='GnBu_r')
        else:
            cmapping = opts.Points(color='grey', colorbar=True)
        hover = HoverTool(tooltips=None)
        xlabel = lookup_latex_label(kdim1)
        ylabel = lookup_latex_label(kdim2)
        popts = opts.Points(
            bgcolor='#E5E9F0',
            fontscale=1.1,
            xlabel=xlabel,
            ylabel=ylabel,
            toolbar='above',
            line_color='black',
            #alpha=0.75, selection_alpha=1, nonselection_alpha=0.1,
            tools=[hover, 'box_select','lasso_select','tap'],
            size=7)
        points = hv.Points(data, kdims=[kdim1, kdim2]).opts(popts, cmapping)
        return points
    
    # bind the widget values to the plotting function so it gets called every time the user interacts with the widget
    # call the bound plotting function inside a holoview DynamicMap object for interaction
    interactive_points = pn.bind(plot_data, kdim1=var1, kdim2=var2, colordim=cmap_var, showcmap=cmap_option)
    points_dmap = hv.DynamicMap(interactive_points, kdims=[]).opts(width=500, height=400, framewise=True)
    
    # define a stream to get a list of all the points the user has selected on the plot
    selection = streams.Selection1D(source=points_dmap)
    
    # formatting the table using plot hooks
    def hook(plot, element):
        plot.handles['table'].autosize_mode = "none"
        for column in plot.handles['table'].columns:
            column.width = 100
    
    # function to generate a table of all the selected points
    def make_table(kdim1, kdim2, colordim):
        table_options = opts.Table(height=300, width=1000, hooks=[hook], bgcolor='#f5f5f5')
        table = hv.DynamicMap(lambda index: hv.Table(data.iloc[index], kdims=[kdim1, kdim2, colordim]), streams=[selection])
        return table.opts(table_options).relabel('Selected Points')
    
    
    # generate the table
    selected_table = pn.bind(make_table, kdim1=var1, kdim2=var2, colordim=cmap_var)
    
    #table_stream = streams.Selection1D(source=selected_table)
    
    # function to run CLASS on data from the selection. 
    # handles the null selection case and multiple selections
    curves = {}
    empty_plot = hv.Curve(np.random.rand(0, 2)).opts(framewise=True)
    def plot_observables(index):
        if not index:
            curves_list = [[empty_plot.relabel('P(k) Residuals - No Selection')], 
                           [empty_plot.relabel('Cl_TT Residuals - No Selection')], 
                           [empty_plot.relabel('Cl_EE Residuals - No Selection')]]
        else:
            new_index = [x for x in index if x not in list(curves.keys())]
            for element in new_index:
                # Need to actually unpack tuple here
                observables = myfunction(element, myfunction_args[0], myfunction_args[1])
                observables_keys = list(observables.keys())

                new_plots = []
                for key in observables_keys:
                    dataset = observables[key]
                    kdim = list(dataset.keys())[0]
                    vdim = list(dataset.keys())[1]
                    plot_observable = hv.Curve(dataset, kdim, vdim, label=key).opts(framewise=True)
                    new_plots.append(plot_observable)
                curves[element] = {plot.label: plot for plot in new_plots}

                # plot_pk_residuals = hv.Curve(observables[observables_keys[0]], 'k', 'Pk').relabel('P(k) Residuals').opts(framewise=True)
                # plot_cl_tt_residuals = hv.Curve(observables[observables_keys[1]], 'l', 'Cl_TT').relabel('Cl_TT Residuals').opts(framewise=True)
                # plot_cl_ee_residuals = hv.Curve(observables[observables_keys[2]], 'l','Cl_EE').relabel('Cl_EE Residuals').opts(framewise=True)
                # curves[element] = {'pk_residuals': plot_pk_residuals, 'cl_tt_residuals': plot_cl_tt_residuals, 'cl_ee_residuals': plot_cl_ee_residuals}
                           
            # pk_curve_list = [curves[key]['pk_residuals'] for key in index]
            # cl_tt_curve_list = [curves[key]['cl_tt_residuals'] for key in index]
            # cl_ee_curve_list = [curves[key]['cl_ee_residuals'] for key in index]
            
            curves_list = []
            for index_item in index:
                curve_types = list(curves[index_item].keys())

            for curve_item in curve_types:
                same_type = [curves[key][curve_item] for key in index]
                curves_list.append(same_type)

        # pk_residuals_overlay = hv.Overlay(pk_curve_list).opts(
        #     opts.Overlay(
        #         xlabel=r'$$k~[h/\mathrm{Mpc}]$$', 
        #         ylabel=r'$$(P(k)-P_{CDM}(k))/P_{CDM}(k)*100~[\%]$$',
        #         show_legend=False))
        # cl_tt_residuals_overlay = hv.Overlay(cl_tt_curve_list).opts(
        #     opts.Overlay(
        #         xlabel=r"$$\ell$$", 
        #         ylabel=r"$$(C_{\ell}^{TT}-C_{\ell, CDM}^{TT})/C_{\ell, CDM}^{TT}*100~[\%]$$",
        #         show_legend=False))
        # cl_ee_residuals_overlay = hv.Overlay(cl_ee_curve_list).opts(
        #     opts.Overlay(
        #         xlabel=r"$$\ell$$", 
        #         ylabel=r"$$(C_{\ell}^{EE}-C_{\ell, CDM}^{EE})/C_{\ell, CDM}^{EE}*100~[\%]$$",
        #         show_legend=False))
        # layout = pk_residuals_overlay + cl_tt_residuals_overlay + cl_ee_residuals_overlay

        layout = hv.Layout()
        for list_of_curves in curves_list:
            overlay = hv.Overlay(list_of_curves)
            layout = layout + overlay
        return layout
    
    
    # put it all together using Panel
    dashboard = pn.Column(pn.Row(var1, var2, cmap_var, cmap_option), pn.Row(points_dmap, selected_table))
    
    if show_observables == True:
        observables_dmap = hv.DynamicMap(plot_observables, streams=[selection]).opts(
            opts.Curve(width=500, height=400, logx=True, padding=0.1, fontscale=1.1, color=hv.Cycle('GnBu'), bgcolor='#22262F', framewise=True), 
            opts.Layout(shared_axes=False),
            opts.Overlay(show_legend=False)
        )
        observables_pane = pn.panel(observables_dmap)
        dashboard = pn.Column(dashboard, observables_pane)
    
    return dashboard
# Read in data
loglkl = ['loglkl']
param_names, latex_params = load_params('../data/chains_planckbossdes_1MeV/2022-11-16_3200000_.paramnames')
params_latex_form = dict(zip(param_names, latex_params))
column_names = loglkl + param_names
df = pd.DataFrame(columns=column_names)
for i in trange(1,5):
    temp = load_data('../data/chains_planckbossdes_1MeV/2022-11-16_3200000__{}.txt'.format(i), column_names=column_names)
    df = pd.concat([df,temp]).reset_index(drop=True)

# prepare data for CLASS computation
# remove nuisance parameters
classy_input = df.drop(columns=['loglkl', 'z_reio', 'A_s', 'sigma8', '100theta_s', 'A_cib_217', 'xi_sz_cib', 'A_sz', 'ps_A_100_100', 'ps_A_143_143', 'ps_A_143_217', 'ps_A_217_217', 'ksz_norm', 'gal545_A_100', 'gal545_A_143', 'gal545_A_143_217', 'gal545_A_217', 'galf_TE_A_100', 'galf_TE_A_100_143', 'galf_TE_A_100_217', 'galf_TE_A_143', 'galf_TE_A_143_217', 'galf_TE_A_217', 'calib_100T', 'calib_217T', 'A_planck', 'b^{(1)}_1', 'b^{(1)}_2', 'b^{(1)}_{G_2}', 'b^{(2)}_1', 'b^{(2)}_2', 'b^{(2)}_{G_2}', 'b^{(3)}_1', 'b^{(3)}_2', 'b^{(3)}_{G_2}', 'b^{(4)}_1', 'b^{(4)}_2', 'b^{(4)}_{G_2}'])
classy_input['omega_b'] = df['omega_b'] * 1e-2
classy_input['sigma_dmeff'] = df['sigma_dmeff'] * 1e-25
classy_input = classy_input.rename(columns={'H0':'h'})
classy_input['h'] = classy_input['h'] * 1e-2
classy_input['f_dmeff'] = 0.1
classy_input['npow_dmeff'] = 0.0
classy_input['Vrel_dmeff'] = 0.0
classy_input['dmeff_target'] = 'baryons'
classy_input['m_dmeff'] = 1e-3

# format for CDM version
#classy_CDM = classy_input.drop(columns=['sigma_dmeff', 'omega_cdm', 'npow_dmeff', 'Vrel_dmeff', 'dmeff_target', 'm_dmeff'])
# classy_CDM = classy_CDM.rename(columns={'omega_dmeff':'omega_cdm'})
classy_CDM = classy_input.drop(columns=['sigma_dmeff', 'npow_dmeff', 'Vrel_dmeff', 'dmeff_target', 'm_dmeff'])


# slice for fast computation
classy_input_slice = classy_input[::500].reset_index(drop=True)
classy_CDM_slice = classy_CDM[::500].reset_index(drop=True)
df_slice = df[::500].reset_index(drop=True)

viz(data=df_slice, myfunction=compute_residuals, myfunction_args=(classy_input_slice, classy_CDM_slice), show_observables=True, latex_dict=params_latex_form).servable()