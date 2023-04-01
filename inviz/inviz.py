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
def plot_points(data):
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
    empty_plot = hv.Curve(np.random.rand(0, 2)).opts(width=500, height=400)

    # run CLASS on data from the selection
    def compute_Pk_on_selection(index):
        # handle the initial case with no selection
        if not index:
            return empty_plot.relabel('P(k) Residuals - no selection')
        
        # create new lists for the user data and the baseline LambdaCDM data
        sel = new_df.iloc[index]
        sel_dict_list = sel.to_dict('records')
        CDM_dict_list = []
        
        # clean up data by removing parameters CLASS doesn't accept
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
        
        # remove parameters that aren't in LambdaCDM
        for k in range(len(sel_dict_list)):
            params_CDM = copy.deepcopy(sel_dict_list[k])
            entries_to_remove2 = ('sigma_dmeff', 'npow_dmeff', 'Vrel_dmeff', 'dmeff_target', 'm_dmeff')
            for l in entries_to_remove2:
                params_CDM.pop(l, None)
            params_CDM['omega_cdm'] = params_CDM.pop('omega_dmeff')
            CDM_dict_list.append(params_CDM)
        
        # compute matter power spectrum of user data
        cosmo = Class()
        cosmo.set(sel_dict_list[0])
        cosmo.set({'output':'mPk', 'P_k_max_1/Mpc':3.0})
        cosmo.compute()
        
        kk = np.logspace(-4,np.log10(3),1000)
        
        Pk1 = []
        h = cosmo.h()
        for k in kk:
            Pk1.append(cosmo.pk(k*h,0.)*h**3)
        
        # compute matter power spectrum of LambdaCDM
        cosmo_CDM = Class()
        cosmo_CDM.set(CDM_dict_list[0])
        cosmo_CDM.set({'output':'mPk', 'P_k_max_1/Mpc':3.0})
        cosmo_CDM.compute()

        Pk_CDM = []
        h = cosmo_CDM.h()
        for k in kk:
            Pk_CDM.append(cosmo_CDM.pk(k*h,0.)*h**3)
        
        # compute residuals and plot them
        residuals = (np.array(Pk1) - np.array(Pk_CDM))/np.array(Pk_CDM)*100
        Pk_residuals = hv.Curve((kk, residuals)).relabel('P(k) Residuals')
        
        return Pk_residuals
    
    # put the plot into a DynamicMap so user can interact
    classy_output_Pk = hv.DynamicMap(compute_Pk_on_selection, kdims=[], streams=[selection]).opts(
        logx=True, 
        width=500, 
        height=400, 
        xlabel=r'$$k~[h/\mathrm{Mpc}]$$', 
        ylabel=r'$$(P(k)-P_{CDM}(k))/P_{CDM}(k)*100~[\%]$$',
        framewise=True
    )
    
    # organize plots
    layout = points + classy_output_Pk
    
    # make a table from the selected data
    def selection_table(index):
        selected_table = hv.Table(ds.iloc[index]).opts(height=200, width=1000, fit_columns=False)
        return selected_table
    
    dashboard = pn.Column(layout, hv.DynamicMap(selection_table, streams=[selection]))
    
    return dashboard
