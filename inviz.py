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
def plot_points(ds, new_df):
    hover = HoverTool(tooltips=None)
    # generate the scatter plot and define it as the source for the "Selection1D" stream
    points = hv.Points(ds).opts(
        color='black',
        alpha=0.5,
        selection_color='red',
        selection_alpha=0.7,
        tools=[hover,
               #'box_select',
               #'lasso_select',
               'tap'],
        size=5,
        width=400,
        height=400,
        axiswise=True)
    selection = streams.Selection1D(source=points)
    
    # run CLASS on data from the selection
    def selection_CLASS(index):
        sel = new_df.iloc[index]
        sel_dict_list = sel.to_dict('records')
        CDM_dict_list = []

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
            
        try:
            cosmo = Class()
            cosmo.set(sel_dict_list[0])
            cosmo.set({'output':'mPk', 'P_k_max_1/Mpc':3.0})
            cosmo.compute()

            kk = np.logspace(-4,np.log10(3),1000)
            Pk1 = []
            h = cosmo.h()
            for k in kk:
                Pk1.append(cosmo.pk(k*h,0.)*h**3)

            cosmo_CDM = Class()
            cosmo_CDM.set(CDM_dict_list[0])
            cosmo_CDM.set({'output':'mPk', 'P_k_max_1/Mpc':3.0})
            cosmo_CDM.compute()

            Pk_CDM = []
            h = cosmo_CDM.h()
            for k in kk:
                Pk_CDM.append(cosmo_CDM.pk(k*h,0.)*h**3)

            residuals = (np.array(Pk1) - np.array(Pk_CDM))/np.array(Pk_CDM)*100
            # plt.xscale('log')
            # plt.plot(kk,residuals)
            # plt.show()
            res_Pk = hv.Curve((kk, residuals), label="Residuals Power Spectrum").opts(
                logx=True, width=600, height=400, shared_axes=False, ylim=(-110,10), padding=0.1, xlabel='k [h/Mpc]', ylabel='(P(k)-P_CDM(k))/P_CDM(k) * 100 [%]')
            return res_Pk

        except IndexError as e:
            print(e)
            xs = np.logspace(-4,np.log10(3),1000)
            ys = np.zeros(1000)
            empty_plot = hv.Curve((xs,ys), label="Residuals Power Spectrum - no selection").opts(
                logx=True, width=600, height=400, shared_axes=False, ylim=(-110,10), padding=0.1, xlabel='k [h/Mpc]', ylabel='(P(k)-P_CDM(k))/P_CDM(k) * 100 [%]')
            return empty_plot
        
    # make a table from the selected data
    def selection_table(index):
        selected_table = hv.Table(ds.iloc[index]).opts(height=200, width=1000, fit_columns=False)
        return selected_table
    
    dashboard = pn.Column(points.opts(shared_axes=False) + hv.DynamicMap(selection_CLASS, streams=[selection]).opts(shared_axes=False), hv.DynamicMap(selection_table, streams=[selection]))
   
    return dashboard
