import pandas as pd
import numpy as np
from glob import iglob
from tqdm import tqdm
from classy import Class
from multiprocessing import Pool

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

# run class on the user's selection with default settings
def run_class(index, sample):
    selection = sample.iloc[[index]].to_dict('index')

    cosmo = Class()
    cosmo.set(selection[index])
    cosmo.set({'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'})
    cosmo.compute()

    # set variables for matter power spectrum and lensed CMB angular power spectra
    kk = np.logspace(-4,np.log10(3),1000)
    Pk = []
    h = cosmo.h()
    for k in kk:
        Pk.append(cosmo.pk(k*h,0.)*h**3)
    Pk = np.array(Pk)
    l = np.array(range(2,2501))
    factor = l*(l+1)/(2*np.pi)
    lensed_cl = cosmo.lensed_cl(2500)
    
    results = [
        {'k': kk, 'Pk': Pk},
        {'l': l, 'Cl_tt': factor*lensed_cl['tt'][2:]},
        {'l': l, 'Cl_ee': factor*lensed_cl['ee'][2:]}, 
    ]
    # cleanups requried for backwards compat w CLASS 2.x
    cosmo.struct_cleanup()
    cosmo.empty()
    return results

# calculate percentage difference between model of interest and LambdaCDM model
def compute_residuals(index, sample, sample_CDM):
    if __name__ == '__main__':
        with Pool() as p:
            [mycosmo, LambdaCDM] = p.starmap(run_class, [(index, sample), (index, sample_CDM)])
    else:
        mycosmo = run_class(index, sample)
        LambdaCDM = run_class(index, sample_CDM)

    myPk, myCl_tt, myCl_ee = mycosmo
    LCDM_Pk, LCDM_Cl_tt, LCDM_Cl_ee = LambdaCDM
    pk_residuals = (myPk['Pk'] - LCDM_Pk['Pk'])/LCDM_Pk['Pk']*100
    cl_tt_residuals = (myCl_tt['Cl_tt'] - LCDM_Cl_tt['Cl_tt'])/LCDM_Cl_tt['Cl_tt']*100
    cl_ee_residuals = (myCl_ee['Cl_ee'] - LCDM_Cl_ee['Cl_ee'])/LCDM_Cl_ee['Cl_ee']*100
    
    residuals = [
        {'k': myPk['k'], 'pk_residuals': pk_residuals}, 
        {'l': myCl_tt['l'], 'cl_tt_residuals': cl_tt_residuals}, 
        {'l': myCl_ee['l'], 'cl_ee_residuals': cl_ee_residuals},
    ]
    return residuals