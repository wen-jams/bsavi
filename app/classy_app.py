import bsavi as bsv
from bsavi import cosmo, loaders
import pandas as pd
import numpy as np
import holoviews as hv
from holoviews import opts


# Read in data
params_with_latex = loaders.load_params('../data/chains_planckbossdes_1MeV/2022-11-16_3200000_.paramnames')
param_names = list(params_with_latex.keys())
chains = loaders.load_chains('../data/chains_planckbossdes_1MeV/*.txt', param_names, params_only=True)
# downsample to avoid overplotting
chains = chains.sample(n=500, random_state=1).reset_index(drop=True)

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
residuals = bsv.Observable(
    name=['P(k) Residuals', 'Cl_TT Residuals', 'Cl_EE Residuals'], 
    myfunc=cosmo.compute_residuals,
    myfunc_args=(classy_input, classy_CDM), 
    plot_type='Curve',
    plot_opts=cosmo_copts,
    latex_labels=resids_latex
)

bsv.viz(data=chains, observables=[residuals], latex_dict=params_with_latex).servable('Fractional IDM')
