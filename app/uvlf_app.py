import inviz as nv
import pandas as pd
import holoviews as hv
from holoviews import opts


binned_df = pd.read_pickle('../data/trey_uvlf/bouwens_2023_data_binned.pkl')
params_df = binned_df[['alphaOutflow', 'alphaStar', 'like', 'timescale', 'velocityOutflow']]
lumfunc_df = binned_df[['uvlf_Muv', 'uvlf_z10.5', 'uvlf_z12.6', 'uvlf_z8.7']]
lumfunc_latex = {
    'alphaOutflow': r'\alpha_{Outflow}',
    'alphaStar': r'\alpha_{Star}',
    'timescale': r'\text{timescale}',
    'velocityOutflow': r'v_{Outflow}',
    'like': r'\text{likelihood}'
}
uvlf_scatter_opts = opts.Scatter(ylim=(1e-11, 1e0), logy=True, invert_xaxis=True, size=5, marker='square')
uvlf_curve_opts = opts.Curve(ylim=(1e-11, 1e0), logy=True, invert_xaxis=True)
uvlf_opts_colored = opts.Curve(ylim=(1e-11, 1e0), logy=True, invert_xaxis=True, color=hv.Cycle('GnBu'), bgcolor='#22262F')

uvlf_latex = {
    'uvlf_Muv': r'\text{UV Magnitude}',
    'uvlf_z10.5': r'\text{Luminosity Function}',
    'uvlf_z12.6': r'\text{Luminosity Function}',
    'uvlf_z8.7': r'\text{Luminosity Function}',
}
uvlf_observables = nv.Observable(
    name=[
        'UVLF at z = 10.5', 
        'UVLF at z = 12.6', 
        'UVLF at z = 8.7'
    ], 
    parameters=[
        {'uvlf_Muv': lumfunc_df['uvlf_Muv'], 'uvlf_z10.5': lumfunc_df['uvlf_z10.5']}, 
        {'uvlf_Muv': lumfunc_df['uvlf_Muv'], 'uvlf_z12.6': lumfunc_df['uvlf_z12.6']}, 
        {'uvlf_Muv': lumfunc_df['uvlf_Muv'], 'uvlf_z8.7': lumfunc_df['uvlf_z8.7']}, 
    ], 
    plot_type=[
        'Curve', 
        'Curve', 
        'Curve', 
    ],
    plot_opts=[
        uvlf_curve_opts, 
        uvlf_curve_opts, 
        uvlf_curve_opts, 
    ],
    latex_labels=uvlf_latex
)

nv.viz(params_df, [uvlf_observables], latex_dict=lumfunc_latex).servable('JWST UVLF')

