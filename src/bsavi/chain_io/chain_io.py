import pandas as pd
import numpy as np
from glob import iglob
from tqdm import tqdm

# methods to process data products from the CLASS cosmology code.

# read in the .paramnames file and return a dict of parameters and their LaTeX formatting
def load_params(filename):
    params_list = []
    with open(filename, 'r') as f:
        for line in f:
            param_and_latex = line.split('\t')
            param_and_latex = [item.strip() for item in param_and_latex]
            params_list.append(param_and_latex)
    return dict(params_list)

# create a DataFrame from the chain files and use a list of parameters as the column names
def load_chains(path, params, params_only=True):
    if isinstance(path, list):
        array_list = [np.loadtxt(filename) for filename in tqdm(path)]
    else: 
        file_list = sorted(iglob(path))
        array_list = [np.loadtxt(filename) for filename in tqdm(file_list)]
    chains = np.vstack(array_list)
    columns = ['weight', '-LogLkl'] + params
    if params_only:
        df = pd.DataFrame(chains[:, 2:], columns=params)
    else:
        df = pd.DataFrame(chains, columns=columns)
    return df
