import holoviews as hv
from holoviews import dim, opts, streams
# from holoviews.selection import link_selections
# import hvplot.pandas
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
# import copy
from multiprocessing import Pool

# pn.extension(loading_spinner='dots', loading_color='#00aa41', sizing_mode="stretch_width")
hv.extension('bokeh')
# hv.Store.set_current_backend('bokeh')
# pn.extension('tabulator')
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
    return results


# generate a scatter plot using the key dimensions from a holoviews.Dataset object, with the CLASS output displayed alongside it
def viz(data, data_classy_input, data_classy_CDM, class_enabled=True, latex_dict=None):
    # handle default case of no latex paramname dictionary
    if latex_dict is None:
        latex_dict = dict()
    # setting Panel widgets for user interaction
    variables = data.columns.values.tolist()
    var1 = pn.widgets.Select(value=variables[0], name='Horizontal Axis', options=variables)
    var2 = pn.widgets.Select(value=variables[1], name='Vertical Axis', options=variables)
    cmap_var = pn.widgets.Select(value=variables[2], name='Colormapped Parameter', options=variables)
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
                cmap='Viridis')
        else:
            cmapping = opts.Points(color='grey', colorbar=True)
        hover = HoverTool(tooltips=None)
        xlabel = lookup_latex_label(kdim1)
        ylabel = lookup_latex_label(kdim2)
        popts = opts.Points(
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
        table_options = opts.Table(height=300, width=1000, hooks=[hook])
        table = hv.DynamicMap(lambda index: hv.Table(data.iloc[index], kdims=[kdim1, kdim2, colordim]), streams=[selection])
        return table.opts(table_options).relabel('Selected Points')
    
    
    # generate the table
    selected_table = pn.bind(make_table, kdim1=var1, kdim2=var2, colordim=cmap_var)
    
    #table_stream = streams.Selection1D(source=selected_table)
    
    # function to run CLASS on data from the selection. 
    # first create an empty plot to handle the null selection case
    empty_plot = hv.Curve(np.random.rand(0, 2))
    def plot_class_results(index):
        if not index:
            empty_pk = empty_plot.relabel('P(k) Residuals - no selection').opts(
                xlabel=r'$$k~[h/\mathrm{Mpc}]$$', 
                ylabel=r'$$(P(k)-P_{CDM}(k))/P_{CDM}(k)*100~[\%]$$')
            empty_cl_tt = empty_plot.relabel('Lensed Cl_TT Residuals - no selection').opts(
                xlabel=r"$$\ell$$", 
                ylabel=r"$$(C_{\ell}^{TT} - C_{\ell, CDM}^{TT})/C_{\ell, CDM}^{TT}*100~[\%]$$")
            empty_cl_ee = empty_plot.relabel('Lensed Cl_EE Residuals - no selection').opts(
                xlabel=r"$$\ell$$", 
                ylabel=r"$$(C_{\ell}^{EE} - C_{\ell, CDM}^{EE})/C_{\ell, CDM}^{EE}*100~[\%]$$")
            empty_layout = empty_pk + empty_cl_tt + empty_cl_ee            
            return empty_layout

        # the Selection1D stream returns an index number. index into the approprate dataframe and turn it into a dictionary for CLASS to read
        selection = data_classy_input.iloc[index]
        selection_CDM = data_classy_CDM.iloc[index]
        sel_dict_list = selection.to_dict('records')
        CDM_dict_list = selection_CDM.to_dict('records')
        
        # compute stats for user's cosmology and LambdaCDM
        # in parallel:
        # if __name__ == '__main__':
        #     with Pool() as p:
        #         [mycosmo, LambdaCDM] = p.map(run_class, [sel_dict_list[0], CDM_dict_list[0]])
        # in serial:
        mycosmo = run_class(sel_dict_list[0])
        LambdaCDM = run_class(CDM_dict_list[0])

        # compute residuals
        pk_residuals = (mycosmo['Pk'] - LambdaCDM['Pk'])/LambdaCDM['Pk']*100
        cl_tt_residuals = (mycosmo['Cl_tt'] - LambdaCDM['Cl_tt'])/LambdaCDM['Cl_tt']*100
        cl_ee_residuals = (mycosmo['Cl_ee'] - LambdaCDM['Cl_ee'])/LambdaCDM['Cl_ee']*100

        plot_pk_residuals = hv.Curve((mycosmo['k'], pk_residuals)).relabel('P(k) Residuals').opts(
            xlabel=r'$$k~[h/\mathrm{Mpc}]$$', 
            ylabel=r'$$(P(k)-P_{CDM}(k))/P_{CDM}(k)*100~[\%]$$')

        plot_cl_tt_residuals = hv.Curve((mycosmo['l'],cl_tt_residuals)).relabel('Cl_TT Residuals').opts(
            xlabel=r"$$\ell$$", 
            ylabel=r"$$(C_{\ell}^{TT}-C_{\ell, CDM}^{TT})/C_{\ell, CDM}^{TT}*100~[\%]$$")

        plot_cl_ee_residuals = hv.Curve((mycosmo['l'],cl_ee_residuals)).relabel('Cl_EE Residuals').opts(
            xlabel=r"$$\ell$$", 
            ylabel=r"$$(C_{\ell}^{EE}-C_{\ell, CDM}^{EE})/C_{\ell, CDM}^{EE}*100~[\%]$$")
        
        layout = (plot_pk_residuals + plot_cl_tt_residuals + plot_cl_ee_residuals)
        return layout
    
    # put it all together using Panel
    dashboard = pn.Column(pn.Row(var1, var2, cmap_var, cmap_option), pn.Row(points_dmap, selected_table))
    
    if class_enabled == True:
        classy_output = hv.DynamicMap(plot_class_results, streams=[selection]).opts(
            opts.Curve(color='black', logx=True, width=500, height=400, padding=0.1, framewise=True),
            opts.Layout(shared_axes=False))
        classy_output_pane = pn.panel(classy_output)
        # pn.param.set_values(classy_output_pane, loading_indicator=True)
        dashboard = pn.Column(dashboard, classy_output_pane)
    
    return dashboard
