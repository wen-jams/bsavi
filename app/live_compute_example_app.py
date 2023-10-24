import bsavi as bsv
import holoviews as hv
from holoviews import opts
import numpy as np
import pandas as pd
from scipy import signal

# Set up the parameters of the problem.
ndim, nsamples = 3, 1000

# Generate some fake data.
np.random.seed(42)
data1 = np.random.randn(ndim * 4 * nsamples // 5).reshape(
    [4 * nsamples // 5, ndim]
)
data2 = 4 * np.random.rand(ndim)[None, :] + np.random.randn(
    ndim * nsamples // 5
).reshape([nsamples // 5, ndim])
data = np.vstack([data1, data2])

param_names = ['frequency', 'phase', 'amplitude']
latex = ['\omega / 2\pi', '\phi', '\mathrm{amplitude}']
df = pd.DataFrame(data, columns=param_names)
latex_dict = dict(zip(param_names, latex))

# write a function that returns multiple waves from the same data
def compute_waveforms(index, input_data):
    selection = input_data.iloc[[index]]
    x = np.linspace(-4*np.pi, 4*np.pi, 1000)
    angular_freq = 2*np.pi*selection['frequency'].iloc[0]
    phase = selection['phase'].iloc[0]
    amp = selection['amplitude'].iloc[0]
    sin = amp * np.sin(angular_freq*x + phase)
    cos = amp * np.cos(angular_freq*x + phase)
    sinc = amp * np.sinc(angular_freq*x/np.pi + phase)
    sawtooth = amp * signal.sawtooth(angular_freq * x + phase)
    waves = [
        {'x': x, 'sin(x)': sin},
        {'x': x, 'sinc(x)': sinc},
        {'x': x, 'sawtooth': sawtooth},
    ]
    return waves

# set some customization options with holoviews opts
opts1 = opts.Curve(xlim=(-4*np.pi, 4*np.pi), color=hv.Cycle('YlOrRd'), bgcolor='#151515')
opts2 = opts.Curve(xlim=(-4*np.pi, 4*np.pi), color=hv.Cycle('PuBuGn'), bgcolor='#151515')
opts3 = opts.Curve(xlim=(-4*np.pi, 4*np.pi), color=hv.Cycle('RdPu'), bgcolor='#f5f5f5')
waves_latex = {
    'x': 'x', 
    'sin(x)': '\sin{x}',
    'sinc(x)': '1/\sin{x}',
    'sawtooth': r'\text{Sawtooth Wave}',
}

# construct the Observable object
waveforms = nv.Observable(
    name=[
        'Sine',
        'Sinc',
        'Sawtooth'
    ],
    myfunc=compute_waveforms,
    myfunc_args=(df,),
    plot_type=[
        'Curve',
        'Curve',
        'Curve',
    ],
    plot_opts=[
        opts1,
        opts2,
        opts3,
    ],
    latex_labels=waves_latex
)

# define another function that returns just one observable
def cosine(index, input_data):
    selection = input_data.iloc[[index]]
    x = np.linspace(-4*np.pi, 4*np.pi, 1000)
    angular_freq = 2*np.pi*selection['frequency'].iloc[0]
    phase = selection['phase'].iloc[0]
    amp = selection['amplitude'].iloc[0]
    cos = amp * np.cos(angular_freq*x + phase)
    waves = [
        {'x': x, 'cos(x)': cos}
    ]
    return waves

cosine_latex = {'x':'x', 'cos(x)': '\cos{x}'}

coswav = nv.Observable(
    name='Cosine',
    myfunc=cosine,
    myfunc_args=(df,),
    plot_type='Curve',
    plot_opts=opts3,
    latex_labels=cosine_latex
)

# visualize both at once
nv.viz(df, [waveforms, coswav], latex_dict=latex_dict).servable('Waveforms')