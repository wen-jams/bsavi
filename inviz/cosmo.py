import pandas as pd
import numpy as np
import re
from classy import Class
from multiprocessing import Pool

# methods to process data products from the CLASS cosmology code.

# read in the .paramnames file and put it into list format
def load_params(filename):
    params_list = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            params = re.split(' \t ', line)
            params_list.append(params)
    return [item[0] for item in params_list], [item[1] for item in params_list]

# create a DataFrame with the chain files as rows and use a list of parameters as the column names
def load_data(filename, column_names):
    data = np.loadtxt(filename)
    df = pd.DataFrame(data[:,1:], columns=column_names)
    return df

# run class on the user's selection
def run_class(selection):
    cosmo = Class()
    cosmo.set(selection)
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
    
    results = {
        'k': kk, 
        'Pk': Pk, 
        'l': l, 
        'Cl_tt': factor*lensed_cl['tt'][2:], 
        'Cl_ee': factor*lensed_cl['ee'][2:], 
    }
    # cleanups reqd for backwards compat w CLASS 2.x
    cosmo.struct_cleanup()
    cosmo.empty()
    return results

# calculate percentage difference between model of interest and LambdaCDM model
def compute_residuals(index, sample, sample_CDM):
    selection = sample.iloc[[index]].to_dict('index')
    selection_CDM = sample_CDM.iloc[[index]].to_dict('index')
    if __name__ == '__main__':
        with Pool() as p:
            [mycosmo, LambdaCDM] = p.map(run_class, [selection[index], selection_CDM[index]])
    else:
        mycosmo = run_class(selection[index])
        LambdaCDM = run_class(selection_CDM[index])

    pk_residuals = (mycosmo['Pk'] - LambdaCDM['Pk'])/LambdaCDM['Pk']*100
    cl_tt_residuals = (mycosmo['Cl_tt'] - LambdaCDM['Cl_tt'])/LambdaCDM['Cl_tt']*100
    cl_ee_residuals = (mycosmo['Cl_ee'] - LambdaCDM['Cl_ee'])/LambdaCDM['Cl_ee']*100
    
    residuals = [
        {'k': mycosmo['k'], 'pk_residuals': pk_residuals}, 
        {'l': mycosmo['l'], 'cl_tt_residuals': cl_tt_residuals}, 
        {'l': mycosmo['l'], 'cl_ee_residuals': cl_ee_residuals},
    ]
    return residuals