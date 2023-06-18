import inviz as nv
import pandas as pd
import numpy as np
import holoviews as hv
from holoviews import opts

from tqdm import trange
import re
from classy import Class
from multiprocessing import Pool

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

copts = opts.Curve(width=500, height=400, logx=True, padding=0.1, fontscale=1.1, color=hv.Cycle('GnBu'), bgcolor='#22262F', framewise=True)
nv.viz(data=df_slice, 
       myfunction=compute_residuals, 
       myfunction_args=(classy_input_slice, classy_CDM_slice), 
       show_observables=True, 
       latex_dict=params_latex_form, 
       curve_opts=copts).servable('Fractional IDM')
