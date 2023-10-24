import pandas as pd
mycosmo = pd.read_json('../data/planck2018/power_spectra_small.json')
chains = mycosmo.drop(columns=['p(k)', 'cl_tt', 'cl_ee'])
class_results = mycosmo[['p(k)', 'cl_tt', 'cl_ee']]

from bsavi.chain_io import load_params

params_with_latex = load_params('../data/planck2018/base_mnu_plikHM_TTTEEE_lowl_lowE_lensing.paramnames')

import bsavi as bsv
import holoviews as hv
from holoviews import opts

curve_opts = opts.Curve(logx=True, color=hv.Cycle('Spectral'))

ps_latex = {
    'k': 'k~[h/\mathrm{Mpc}]',
    'Pk': 'P(k)',
    'l': '\ell',
    'Cl_tt': '[{\ell(\ell+1)}/{2\pi}]~C_{\ell}^{TT}',
    'Cl_ee': '[{\ell(\ell+1)}/{2\pi}]~C_{\ell}^{EE}',
}

power_spectra = bsv.Observable(
    name=['P(k)', 'Lensed Cl_TT', 'Lensed Cl_EE'], 
    parameters=class_results,
    plot_type='Curve',
    plot_opts=curve_opts,
    latex_labels=ps_latex
)

bsv.viz(chains, [power_spectra], latex_dict=params_with_latex).servable()