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
def plot_points(ds, df):
    hover = HoverTool(tooltips=None)
    # generate the scatter plot and define it as the source for the "Selection1D" stream
    points = hv.Points(ds).opts(
        color='black',
        alpha=0.5,
        selection_alpha=1,
        nonselection_alpha=0.1,
        tools=[hover,'box_select','lasso_select','tap'],
        size=5,
        width=400,
        height=400)

    selection = streams.Selection1D(source=points)
    empty_plot = hv.Curve(np.random.rand(0, 2))


    # run CLASS on data from the selection
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

        sel = df.iloc[index]
        sel_dict_list = sel.to_dict('records')
        CDM_dict_list = []

        # remove nuisance parameters and add new ones. in the future this stage will be specified by the user instead of hard-coded
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

        # run class on the user's data
        cosmo = Class()
        cosmo.set(sel_dict_list[0])
        cosmo.set({'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'})
        cosmo.compute()

        # get class compute products
        kk = np.logspace(-4,np.log10(3),1000)
        Pk1 = []
        h = cosmo.h()
        for k in kk:
            Pk1.append(cosmo.pk(k*h,0.)*h**3)

        l = np.array(range(2,2501))
        factor = l*(l+1)/(2*np.pi)
        lensed_cl = cosmo.lensed_cl(2500)

        # run class on LambdaCDM model
        cosmo_CDM = Class()
        cosmo_CDM.set(CDM_dict_list[0])
        cosmo_CDM.set({'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'})
        cosmo_CDM.compute()

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
        plot_cl_tt_residuals = hv.Curve((l,factor*cl_tt_residuals)).relabel('Cl_TT Residuals').opts(
            xlabel=r"$$\ell$$", 
            ylabel=r"$$(C_{\ell}^{TT}-C_{\ell, CDM}^{TT})/C_{\ell, CDM}^{TT}*100~[\%]$$")
        plot_cl_ee_residuals = hv.Curve((l,factor*cl_ee_residuals)).relabel('Cl_EE Residuals').opts(
            xlabel=r"$$\ell$$", 
            ylabel=r"$$(C_{\ell}^{EE}-C_{\ell, CDM}^{EE})/C_{\ell, CDM}^{EE}*100~[\%]$$")
        layout = (plot_pk_residuals + plot_cl_tt_residuals + plot_cl_ee_residuals)
        return layout


    classy_output = hv.DynamicMap(run_class_on_selection, streams=[selection]).opts(
        opts.Curve(logx=True, width=500, height=400, padding=0.1, framewise=True),
        opts.Layout(shared_axes=False))


    # generate a table of all the selected points on the point plot
    def make_table(dataset, stream):
        table = hv.DynamicMap(lambda index: hv.Table(dataset.iloc[index]), streams=[stream])
        return table

    # formatting the table with plot hooks
    def hook(plot, element):
        plot.handles['table'].autosize_mode = "none"
        for column in plot.handles['table'].columns:
            column.width = 100


    table_options = opts.Table(height=200, width=1050, hooks=[hook])
    selected_table = make_table(ds, selection).opts(table_options)

    # put it all together
    points_and_table = points + selected_table
    points_and_table = points_and_table.opts(shared_axes=False)
    dashboard = pn.Column(points_and_table, classy_output)
    return dashboard
    