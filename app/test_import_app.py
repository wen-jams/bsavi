import inviz as nv
import pandas as pd
import holoviews as hv
from holoviews import opts

interp_df = pd.read_pickle('../data/trey_uvlf/bouwens_2023_data.pkl')
binned_df = pd.read_pickle('../data/trey_uvlf/bouwens_2023_data_binned.pkl')
params_df = interp_df[['alphaOutflow', 'alphaStar', 'like', 'timescale', 'velocityOutflow']]
lumfunc_df = interp_df[['uvlf_Muv', 'uvlf_z10.5', 'uvlf_z12.6', 'uvlf_z8.7']]
uvlf = {}
for row in lumfunc_df.index:
    uvlf[row] = {
        'z = 10.5': {'uvlf_Muv': lumfunc_df['uvlf_Muv'][row], 'uvlf_z10.5': lumfunc_df['uvlf_z10.5'][row]}, 
        'z = 12.6': {'uvlf_Muv': lumfunc_df['uvlf_Muv'][row], 'uvlf_z12.6': lumfunc_df['uvlf_z12.6'][row]}, 
        'z = 8.7': {'uvlf_Muv': lumfunc_df['uvlf_Muv'][row], 'uvlf_z8.7': lumfunc_df['uvlf_z8.7'][row]}, 
    }
reshaped_uvlf = pd.DataFrame.from_dict(uvlf, orient='index')

uvlf_opts = opts.Curve(ylim=(1e-11, None), logy=True, invert_xaxis=True, color=hv.Cycle('GnBu'), bgcolor='#22262F', height=400, width=500)
nv.viz(data=params_df, data_observable=reshaped_uvlf, curve_opts=uvlf_opts).servable('JWST UV LumFunc')