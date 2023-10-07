import inviz as nv
from inviz import cosmo
import pandas as pd
import numpy as np
from tqdm import trange
import holoviews as hv
from holoviews import opts


# Read in data
param_names, latex_params = cosmo.load_params('../data/chains_planckbossdes_1MeV/2022-11-16_3200000_.paramnames')
params_latex_form = dict(zip(param_names, latex_params))
column_names = ['loglkl'] + param_names
chains = pd.DataFrame(columns=column_names)
for i in trange(1,5):
    temp = cosmo.load_data('../data/chains_planckbossdes_1MeV/2022-11-16_3200000__{}.txt'.format(i), column_names=column_names)
    chains = pd.concat([chains,temp]).reset_index(drop=True)
# Move the loglkl column to the third position (inviz colormaps the third column by default)
column_to_move = chains.pop('loglkl')
chains.insert(2, 'loglkl', column_to_move)
# Slice the dataset to avoid overplotting
chains = chains[::1000].reset_index(drop=True)

# prepare data for CLASS computation
# remove nuisance parameters
classy_input = chains.loc[:, ('omega_b', 'omega_cdm', 'ln10^{10}A_s', 'n_s', 'tau_reio', 'sigma_dmeff', 'Omega_Lambda', 'YHe', 'H0')]
classy_input['omega_b'] = classy_input['omega_b'] * 1e-2
classy_input['sigma_dmeff'] = classy_input['sigma_dmeff'] * 1e-25
classy_input = classy_input.rename(columns={'H0':'h'})
classy_input['h'] = classy_input['h'] * 1e-2
classy_input['f_dmeff'] = 0.1
classy_input['npow_dmeff'] = 0.0
classy_input['Vrel_dmeff'] = 0.0
classy_input['dmeff_target'] = 'baryons'
classy_input['m_dmeff'] = 1e-3

# format for CDM version
classy_CDM = classy_input.drop(columns=['sigma_dmeff', 'npow_dmeff', 'Vrel_dmeff', 'dmeff_target', 'm_dmeff'])

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
    myfunc_args=(classy_input, classy_CDM), 
    plot_type='Curve',
    plot_opts=cosmo_copts,
    latex_labels=resids_latex
)

nv.viz(data=chains, observables=[residuals], latex_dict=params_latex_form).servable('Fractional IDM')
