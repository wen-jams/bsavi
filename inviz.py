import holoviews as hv
from holoviews import dim, opts
import hvplot.pandas
import pandas as pd
from itertools import combinations
import numpy as np
from tqdm import tqdm
import re
from bokeh.plotting import show

hv.extension('bokeh', width=100)
hv.Store.set_current_backend('bokeh')

# hv.extension('bokeh')


def load_params(filename):
    params_list = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            params = re.split(' \t ', line)
            params_list.append(params)
    return [item[0] for item in params_list]


def load_data(filename, column_names):
    data = np.loadtxt(filename)
    df = pd.DataFrame(data[:, 2:], columns=column_names)
    return df


def plot_scat_bivar(params, df):
    pairs = [list(comb) for comb in combinations(params, 2)]

    # Consider swapping to hv.Points and forcing the hover via the hextiles instead of the scatter?
    scat = df.hvplot.scatter(pairs[0][0], pairs[0][1], alpha=0, c='lightgrey', marker='s', size=50, hover_cols=params)
    hex = hv.HexTiles(df[[pairs[0][0], pairs[0][1]]].values, [pairs[0][0], pairs[0][1]], []).opts(
        opts.HexTiles(scale=(dim('Count').norm() * 0.5) + 0.3, bgcolor="black", colorbar=False, cmap="kbc",
                      color_levels=20))
    bivar = hv.Bivariate(df[[pairs[0][0], pairs[0][1]]].values, [pairs[0][0], pairs[0][1]], []).opts(
        opts.Bivariate(bandwidth=0.5, cut=0, levels=5, cmap=['#ffffff'], colorbar=False, show_legend=False,
                       filled=False, toolbar='above', width=350, alpha=0.8))
    overlay = (scat * hex * bivar).opts(width=400, height=400)

    for param_a, param_b in pairs[1:]:
        scat = df.hvplot.scatter(param_a, param_b, alpha=0, c='lightgrey', size=50, marker='s', hover_cols=params)
        hex = hv.HexTiles(df[[param_a, param_b]].values, [param_a, param_b], []).opts(
            opts.HexTiles(scale=(dim('Count').norm() * 0.5) + 0.3, bgcolor="black", colorbar=False, cmap="kbc",
                          color_levels=20))
        bivar = hv.Bivariate(df[[param_a, param_b]].values, [param_a, param_b], []).opts(
            opts.Bivariate(bandwidth=0.5, cut=0, levels=5, cmap=['#ffffff'], colorbar=False, show_legend=False,
                           filled=False, toolbar='above', width=350, alpha=0.8))

        overlay += (scat * hex * bivar).opts(width=400, height=400)

    return overlay


if __name__ == '__main__':
    # Read in data
    param_names = load_params('data/test_IDM_n_0/2022-05-04_75000_.paramnames')
    df = pd.DataFrame(columns=param_names)
    for i in tqdm(range(1, 56)):
        temp = load_data('data/test_IDM_n_0/2022-05-04_75000__{}.txt'.format(i), column_names=param_names)
        df = pd.concat([df, temp]).reset_index(drop=True)

    # Plot that bih (slicing by 30 because I can't be bothered to wait...)
    params = ['omega_b', 'omega_dmeff', 'n_s', 'tau_reio', 'sigma_dmeff', 'H0', 'A_s', 'sigma8']
    plot = plot_scat_bivar(params, df[::30])
    # show(hv.render(plot.cols(7)))
