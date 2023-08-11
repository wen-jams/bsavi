import pandas as pd
import numpy as np
import inviz as iv
import holoviews as hv
from holoviews import opts

like = pd.DataFrame(np.random.rand(100, 4), columns=list('ABCD'))
like_latex = {'A': r'\alpha',
              'B': r'\beta',
              'C': r'\gamma',
              'D': r'\delta'}
poly_xs = []
poly_ys = []
for i in range(0,100):
    x = np.linspace(0, 10, 100)
    poly_xs.append(x)
    y = like.at[i, 'A'] * x**like.at[i, 'B'] * like.at[i, 'C'] * x**like.at[i, 'D']
    poly_ys.append(y)

sin_xs = []
sin_ys = []
for i in range(0,100):
    x = np.linspace(-2*np.pi, 2*np.pi, 100)
    sin_xs.append(x)
    y = like.at[i, 'A'] * np.sin(like.at[i, 'B'] * x) + like.at[i, 'C'] * np.sin(like.at[i, 'D'] * x)
    sin_ys.append(y)


poly = pd.DataFrame({'x': poly_xs, 'y': poly_ys})
poly_latex = {'x': 'x', 'y': r'\alpha x^{\beta} + \gamma x^{\delta}'}

sin = pd.DataFrame({'x': sin_xs, 'y': sin_ys})
sin_latex = {'x': 'x', 'y': r'\alpha \sin{\beta x} + \gamma \sin{\delta x}'}

poly_opts = opts.Curve(framewise=True)
sin_opts = opts.Curve(framewise=True)

polynomials = iv.Observable(name='polynomials', parameters=[poly], plot_type=['Curve'], plot_opts=poly_opts, latex_labels=poly_latex)
sine_wave = iv.Observable(name='Composite Sine Wave', parameters=[sin], plot_type=['Curve'], plot_opts=sin_opts, latex_labels=sin_latex)
iv.viz(like, observables=[polynomials, sine_wave], latex_dict=like_latex).servable()