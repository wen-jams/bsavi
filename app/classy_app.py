import inviz as nv
from inviz import cosmo
import pandas as pd
import numpy as np
from tqdm import trange
import holoviews as hv
from holoviews import opts


# Read in data
loglkl = ['loglkl']
param_names, latex_params = cosmo.load_params('../data/chains_planckbossdes_1MeV/2022-11-16_3200000_.paramnames')
params_latex_form = dict(zip(param_names, latex_params))
column_names = loglkl + param_names
df = pd.DataFrame(columns=column_names)
for i in trange(1,5):
    temp = cosmo.load_data('../data/chains_planckbossdes_1MeV/2022-11-16_3200000__{}.txt'.format(i), column_names=column_names)
    df = pd.concat([df,temp]).reset_index(drop=True)

# prepare data for CLASS computation
# remove nuisance parameters
classy_input = df.drop(
    columns=[
        'loglkl', 
        'z_reio', 
        'A_s', 
        'sigma8', 
        '100theta_s', 
        'A_cib_217', 
        'xi_sz_cib', 
        'A_sz', 
        'ps_A_100_100', 
        'ps_A_143_143', 
        'ps_A_143_217', 
        'ps_A_217_217', 
        'ksz_norm', 
        'gal545_A_100', 
        'gal545_A_143', 
        'gal545_A_143_217', 
        'gal545_A_217', 
        'galf_TE_A_100', 
        'galf_TE_A_100_143', 
        'galf_TE_A_100_217', 
        'galf_TE_A_143', 
        'galf_TE_A_143_217', 
        'galf_TE_A_217', 
        'calib_100T', 
        'calib_217T', 
        'A_planck', 
        'b^{(1)}_1', 
        'b^{(1)}_2', 
        'b^{(1)}_{G_2}', 
        'b^{(2)}_1', 
        'b^{(2)}_2', 
        'b^{(2)}_{G_2}', 
        'b^{(3)}_1', 
        'b^{(3)}_2', 
        'b^{(3)}_{G_2}', 
        'b^{(4)}_1', 
        'b^{(4)}_2', 
        'b^{(4)}_{G_2}'
    ]
)
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

cosmo_copts = opts.Curve(
    logx=True, 
    color=hv.Cycle('GnBu'), 
    bgcolor='#22262F', 
    framewise=True
)
resids_latex = {
    'k': 'k~[h/\mathrm{Mpc}]',
    'pk_residuals': '(P(k)-P_{CDM}(k))/P_{CDM}(k)*100~[\%]',
    'l': '\ell',
    'cl_tt_residuals': '(C_{\ell}^{TT}-C_{\ell, CDM}^{TT})/C_{\ell, CDM}^{TT}*100~[\%]',
    'cl_ee_residuals': '(C_{\ell}^{EE}-C_{\ell, CDM}^{EE})/C_{\ell, CDM}^{EE}*100~[\%]',
}
residuals = nv.Observable(
    name=['P(k) Residuals', 'Cl_TT Residuals', 'Cl_EE Residuals'], 
    myfunc=cosmo.compute_residuals,
    myfunc_args=(classy_input_slice, classy_CDM_slice), 
    plot_type='Curve',
    plot_opts=cosmo_copts,
    latex_labels=resids_latex
)

nv.viz(data=df_slice, observables=[residuals], latex_dict=params_latex_form).servable('Fractional IDM')
