import inviz as nv
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

def example_observables(index, input_data):
    selection = input_data.iloc[[index]]
    x = np.linspace(-2*np.pi, 2*np.pi, 201)
    angular_freq = 2*np.pi*float(selection['frequency'])
    phase = float(selection['phase'])
    amp = float(selection['amplitude'])
    sin = amp * np.sin(angular_freq*x + phase)
    cos = amp * np.cos(angular_freq*x + phase)
    sinc = amp * np.sinc(angular_freq*x/np.pi + phase)
    sawtooth = amp * signal.sawtooth(angular_freq * x + phase)
    funcs = {
        'Sine': {'x': x, 'sin(x)': sin}, 
        # 'Cosine': {'x': x, 'cos(x)': cos},
        'Sinc': {'x': x, 'sinc(x)': sinc}, 
        'Sawtooth': {'x': x, 'sawtooth(x)': sawtooth}}
    return funcs

exopts = opts.Curve(xlim=(-2*np.pi, 2*np.pi), height=400, width=500, color=hv.Cycle('GnBu'), bgcolor='#22262F')
nv.viz(data=df, myfunction=example_observables, myfunction_args=(df,), show_observables=True, latex_dict=latex_dict, curve_opts=exopts).servable('Waveforms')