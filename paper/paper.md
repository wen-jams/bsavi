---
title: 'BSAVI:Bayesian Sample Visualizer for Cosmological Likelihoods'
tags:
- Python
- interactive
- visualization
- Bayesian statistics
authors:
- name: James S. Wen
  orcid: 0009-0009-3828-0267
  corresponding: True
  affiliation: 1 # (Multiple affiliations must be quoted)
- name: Karime Maamari
  affiliation: 1
- name: Adam He
  affiliation: 1
- name: Trey Driskell
  affiliation: 1
- name: Timothy Morton
  affiliation: 1
- name: Vera Gluscevic
  affiliation: 1
affiliations:
- name: University of Southern California
  index: 1
date: 29 December 2023
bibliography: paper.bib
---

# Summary

Scientists in many fields seek to explain or predict real-world phenomena with theoretical models. These models typically have input parameters which affect the prediction, such as how the number of days without rain could increase the probability of a wildfire starting. We can refine our model through Bayesian inference: as we observe wildfires, we can record how long that region has been in drought. Prior to recording this data, we had a “degree of belief” in our model (this is the Bayesian definition of prior probability). Perhaps drought and wildfire frequency are not as tightly correlated as we thought. We can then update our beliefs with this new set of data using Bayes’ Theorem:

$$
P(H|E) = \frac{P(E|H)P(H)}{P(E)}
$$

Where $P(H|E)$ is the posterior probability of our hypothesis H being true, given the evidence $E$; $P(E|H)$ is the probability of observing such evidence, assuming our hypothesis is true; $P(H)$ is the probability that our hypothesis is true prior to observing the evidence; and $P(E)$ is the marginal likelihood, which is constant for all hypotheses being considered.

Bayesian inference is a method for inferring model parameters from observational data, often used in physics and astronomy. It yields a posterior probability density function which can be used to identify what model parameters are consistent with the observational data. This posterior can be sampled using Markov chain Monte Carlo (MCMC) methods, resulting in a set of parameter values whose distribution approximates the posterior probability density function.

BSAVI is a tool for exploratory analysis of this sample distribution of the posterior probability, and how it relates to the corresponding data space. Models with multiple parameters have high-dimensional posteriors, which makes them difficult to visualize. Additionally, it is often useful to see how a sample from the posterior (parameter space) translates into real-world observables (data space). To enable this, BSAVI has a built-in Observable class, which allows for easy annotation and plotting of each observable dataset. It can also take callables, so any preexisting code can be used with minimal modifications to compute observables on the fly. BSAVI builds on the Holoviz libraries, including `holoviews` and `panel`, with `bokeh` as the interactive plotting backend.

# Statement of Need

BSAVI was originally developed for applications in cosmology. Inference exercises for any cosmological model requires a thorough understanding of its parameter space. For example, a model which allows self-interacting neutrinos [@he2023selfinteracting] would lead to observable changes in the distribution of matter in the universe and the anisotropies of the cosmic microwave background. These observables can be computed from the model parameters using the Cosmic Linear Anisotropy Solving System (CLASS) [@Diego_Blas_2011] and compared to real-world observational data. Finding the parameter values that best fit this data then requires MCMC sampling the Bayesian posterior.

 The existing tools for visualizing the relationship between samples returned by MCMC and cosmological observables were separate and static, while a unified and interactive experience was desired. For example, a common method of visualizing the likelihood was to make pair plots of the parameters. A purpose-built package like corner is often used for this function. However, with high-dimensional likelihoods the number of pairs increases, and the resulting figure can become difficult to analyze. Additionally, `corner` [@corner] and many other plotting tools use `matplotlib` as their backend, making it hard to interactively explore the dataset. There is a strong desire to see how a specific subset of the samples are distributed across the parameter space, as well as what their corresponding observables look like.

We solve this by providing researchers with an easy way to declare their observables, link them to a set of samples, and visualize them in an interactive dashboard. The user may supply their own function for BSAVI to dynamically compute observables, or a precomputed data table of the same length as their sample data. In the second case, the two tables will be linked by their indices.

# Example

In 2018, the Planck Collaboration published cosmological parameters derived from measurements of CMB anisotropies [@2020]. In \autoref{fig1} we use BSAVI to visualize the effect different parameter values have on the CMB anisotropies represented by $C_{l}^{EE}$ and $C_{l}^{TT}$, and the clustering of matter represented by $P(k)$.

![Three samples from the Planck 2018 results, selected by the user, and their corresponding observables. On the upper left is a 2D slice of the sample distribution, with dropdown menus to modify the parameters on each axis and an optional colormapped parameter. The bottom left corner is a table of all the selected samples, which can be sorted by any parameter. Once a selection has been made, its corresponding Observable data is plotted in the panels on the right.\label{fig1}](fig1.png)

This visualization was produced in `class_file_reading.ipynb`, one of several tutorial notebooks in the [BSAVI repository](https://github.com/wen-jams/bsavi/tree/main/tutorials). These notebooks demonstrate how BSAVI can be seamlessly incorporated in an exploratory data analysis session with cosmological data as an example. The code from this notebook is reproduced below, with brief explanations for each section.

First load the `power_spectra_small.json` file, which contains a small sample of the Planck 2018 chains along with their power spectra computed by CLASS:

```python
import pandas as pd
import bsavi as bsv
from bsavi.loaders import load_params

planck = pd.read_json('../data/planck2018/power_spectra_small.json')
chains = planck.drop(columns=['p(k)', 'cl_tt', 'cl_ee'])
class_results = planck[['p(k)', 'cl_tt', 'cl_ee']]
```

Next use `load_params` to read the `.paramnames` file into a dictionary of plain-text parameter labels and their LaTeX formatting:

```python
params_with_latex = load_params(
        '../data/planck2018/base_mnu_plikHM_TTTEEE_lowl_lowE_lensing.paramnames')
```

Two more attributes, plot_opts and latex_labels, can be used for setting plot style options and LaTeX axis labels for the Observable plots. To set them, add the following to your code:

```python
from holoviews import opts

curve_opts = opts.Curve(logx=True)

ps_latex = {
    'k': 'k~[h/\mathrm{Mpc}]',
    'Pk': 'P(k)',
    'l': '\ell',
    'Cl_tt': '[{\ell(\ell+1)}/{2\pi}]~C_{\ell}^{TT}',
    'Cl_ee': '[{\ell(\ell+1)}/{2\pi}]~C_{\ell}^{EE}',
}

power_spectra = bsv.Observable(
    name=['P(k)', 'Lensed Cl_TT', 'Lensed Cl_EE'], 
    data=class_results,
    plot_type='Curve',
    plot_opts=curve_opts,
)
```

Note that the keys of the LaTeX dict match the column names of the power_spectra dataframe.

Then, we can use the viz function to generate the interactive dashboard:

```python
bsv.viz(data=chains, observables=[power_spectra],
        latex_dict=params_with_latex).servable()
```

The app launches a Panel server, and as such can be viewed inline when running in a Jupyter Notebook or JupyterLab, or as a separate browser window if run as a python script using `panel serve my_script.py`.

This example and more tutorials, including how to create dynamically computed Observables, can be found on the [documentation page](https://wen-jams.github.io/bsavi/).

# References
