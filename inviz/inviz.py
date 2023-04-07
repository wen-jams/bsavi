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

hv.extension('bokeh')
hv.Store.set_current_backend('bokeh')
pn.extension('tabulator')
pn.extension()

# read in the .paramnames file and put it into list format
def load_params(filename):
    params_list = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            params = re.split(' \t ', line)
            params_list.append(params)
    return [item[0] for item in params_list]


# create a DataFrame with the chain files as rows and use a list of parameters as the column names
def load_data(filename, column_names):
    data = np.loadtxt(filename)
    df = pd.DataFrame(data[:,2:], columns=column_names)
    return df


# generate a scatter plot using the key dimensions from a holoviews.Dataset object, with the CLASS output displayed alongside it
def viz(dataset, dataframe):
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
        popts = opts.Points(
            toolbar='above',
            #line_color='black',
            #alpha=0.75, selection_alpha=1, nonselection_alpha=0.1,
            tools=[hover, 'box_select','lasso_select','tap'],
            size=7)
        points = hv.Points(dataframe, kdims=[kdim1, kdim2]).opts(popts, cmapping)
        return points
    
    
    # setting Panel widgets for user interaction
    variables = dataframe.columns.values.tolist()
    var1 = pn.widgets.Select(value=variables[0], name='Horizontal Axis', options=variables)
    var2 = pn.widgets.Select(value=variables[1], name='Vertical Axis', options=variables)
    cmap_var = pn.widgets.Select(value=variables[2], name='Colormapped Parameter', options=variables)
    cmap_option = pn.widgets.Checkbox(value=True, name='Show Colormap', align='end')
    
    # bind the widget values to the plotting function so it gets called every time the user interacts with the widget
    # call the bound plotting function inside a holoview DynamicMap object for interaction
    interactive_points = pn.bind(plot_data, kdim1=var1, kdim2=var2, colordim=cmap_var, showcmap=cmap_option)
    points_dmap = hv.DynamicMap(interactive_points, kdims=[]).opts(width=500, height=400, framewise=True)
    
    # define a stream to get a list of all the points the user has selected on the plot
    selection = streams.Selection1D(source=points_dmap)
    
    # function to generate a table of all the selected points
    def make_table(kdim1, kdim2, colordim):
        table = hv.DynamicMap(lambda index: hv.Table(dataframe.iloc[index], kdims=[kdim1, kdim2, colordim]), streams=[selection])
        # formatting the table using plot hooks and a holoviews Options object
        def hook(plot, element):
            plot.handles['table'].autosize_mode = "none"
            for column in plot.handles['table'].columns:
                column.width = 100
            
        table_options = opts.Table(height=300, width=1000, hooks=[hook])
        return table.opts(table_options).relabel('Selected Points')
    
    
    # generate the table
    selected_table = pn.bind(make_table, kdim1=var1, kdim2=var2, colordim=cmap_var)
    
    # function to run CLASS on data from the selection. 
    # first create an empty plot to handle the null selection case
    empty_plot = hv.Curve(np.random.rand(0, 2))
    def run_class_on_selection(index):
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

        # the Selection1D stream returns a dict. turn it into a list
        sel = df.iloc[index]
        sel_dict_list = sel.to_dict('records')
        CDM_dict_list = []
        
        # remove nuisance parameters and add some project-specific ones. in the future these will be defined by the user
        for i in range(len(sel_dict_list)):
            entries_to_remove1 = ('z_reio', 'A_s', 'sigma8', '100theta_s', 'A_cib_217', 'xi_sz_cib', 'A_sz', 'ps_A_100_100', 'ps_A_143_143', 'ps_A_143_217', 'ps_A_217_217', 'ksz_norm', 
                                 'gal545_A_100', 'gal545_A_143', 'gal545_A_143_217', 'gal545_A_217', 'galf_TE_A_100', 'galf_TE_A_100_143', 'galf_TE_A_100_217', 'galf_TE_A_143', 'galf_TE_A_143_217', 
                                 'galf_TE_A_217', 'calib_100T', 'calib_217T', 'A_planck' )
            for j in entries_to_remove1:
                sel_dict_list[i].pop(j, None)

            sel_dict_list[i]['omega_b'] = sel_dict_list[i]['omega_b']*1e-2
            sel_dict_list[i]['sigma_dmeff'] = sel_dict_list[i]['sigma_dmeff']*1e-25
            sel_dict_list[i]['h'] = (sel_dict_list[i].pop('H0'))*1e-2
            sel_dict_list[i].update({"omega_cdm":1e-15, "npow_dmeff": 0, "Vrel_dmeff": 0, "dmeff_target": "baryons", "m_dmeff": 1e-3})

        for k in range(len(sel_dict_list)):
            params_CDM = copy.deepcopy(sel_dict_list[k])
            entries_to_remove2 = ('sigma_dmeff', 'npow_dmeff', 'Vrel_dmeff', 'dmeff_target', 'm_dmeff')
            for l in entries_to_remove2:
                params_CDM.pop(l, None)
            params_CDM['omega_cdm'] = params_CDM.pop('omega_dmeff')
            CDM_dict_list.append(params_CDM)

        # run class on the user's selection
        cosmo = Class()
        cosmo.set(sel_dict_list[0])
        cosmo.set({'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'})
        cosmo.compute()

        # set variables for matter power spectrum and lensed CMB angular power spectra
        kk = np.logspace(-4,np.log10(3),1000)
        Pk1 = []
        h = cosmo.h()
        for k in kk:
            Pk1.append(cosmo.pk(k*h,0.)*h**3)

        l = np.array(range(2,2501))
        factor = l*(l+1)/(2*np.pi)
        lensed_cl = cosmo.lensed_cl(2500)
        
        # run CLASS on the user's selection using the CDM model
        cosmo_CDM = Class()
        cosmo_CDM.set(CDM_dict_list[0])
        cosmo_CDM.set({'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'})
        cosmo_CDM.compute()

        # set variables for CDM observables
        Pk_CDM = []
        h = cosmo_CDM.h()
        for k in kk:
            Pk_CDM.append(cosmo_CDM.pk(k*h,0.)*h**3)

        lensed_cl_CDM = cosmo_CDM.lensed_cl(2500)

        # compute residuals and plot them
        pk_residuals = (np.array(Pk1) - np.array(Pk_CDM))/np.array(Pk_CDM)*100
        cl_tt_residuals = (lensed_cl['tt'][2:] - lensed_cl_CDM['tt'][2:])/(lensed_cl_CDM['tt'][2:])*100
        cl_ee_residuals = (lensed_cl['ee'][2:] - lensed_cl_CDM['ee'][2:])/(lensed_cl_CDM['ee'][2:])*100

        plot_pk_residuals = hv.Curve((kk, pk_residuals)).relabel('P(k) Residuals').opts(
            xlabel=r'$$k~[h/\mathrm{Mpc}]$$', 
            ylabel=r'$$(P(k)-P_{CDM}(k))/P_{CDM}(k)*100~[\%]$$')

        plot_cl_tt_residuals = hv.Curve((l,cl_tt_residuals)).relabel('Cl_TT Residuals').opts(
            xlabel=r"$$\ell$$", 
            ylabel=r"$$(C_{\ell}^{TT}-C_{\ell, CDM}^{TT})/C_{\ell, CDM}^{TT}*100~[\%]$$")

        plot_cl_ee_residuals = hv.Curve((l,cl_ee_residuals)).relabel('Cl_EE Residuals').opts(
            xlabel=r"$$\ell$$", 
            ylabel=r"$$(C_{\ell}^{EE}-C_{\ell, CDM}^{EE})/C_{\ell, CDM}^{EE}*100~[\%]$$")
        
        layout = (plot_pk_residuals + plot_cl_tt_residuals + plot_cl_ee_residuals)
        return layout
    

    classy_output = hv.DynamicMap(run_class_on_selection, streams=[selection]).opts(
        opts.Curve(color='black', logx=True, width=500, height=400, padding=0.1, framewise=True),
        opts.Layout(shared_axes=False))

    # put it all together using Panel
    points_display = pn.Column(pn.Row(var1, var2, cmap_var, cmap_option), pn.Row(points_dmap, selected_table))
    dashboard = pn.Column(points_display, classy_output)
    return dashboard
