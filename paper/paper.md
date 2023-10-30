---
title: 'BSAVI:Bayesian Sample Visualizer for Cosmological Likelihoods'
tags:
- Python
- interactive
- visualization
- Bayesian statistics
- 
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
- name: University of Southern California, USA
  index: 1
date: 30 October 2023
bibliography: paper.bib
---

# Summary

Scientists in many fields seek to explain or predict real-world phenomena with a theoretical model. These models typically have input parameters which affect the prediction, such as how the number of days without rain could increase the probability of a wildfire starting. We can refine our model through Bayesian inference: as we see wildfires, we can record how long that region has been in drought. Prior to recording this data, we had a “degree of belief” in our model (this is the Bayesian definition of prior probability). Perhaps drought and wildfire frequency are not as tightly correlated as we thought. We can then update our beliefs with this new set of data using Bayes’ Theorem:

$$
P(H|E) = \frac{P(E|H)P(H)}{P(E)}
$$

Where:

- P(H|E) is the posterior probability of our hypothesis H being true, given the evidence E;
- P(E|H) is the probability of observing such evidence, assuming our hypothesis is true;
- P(H) is the probability that our hypothesis is true prior to observing the evidence; and
- P(E) is the marginal likelihood, which is constant for all hypotheses being considered.

Bayesian inference is a method for inferring model parameters from observational data, often used in physics and astronomy. It yields a posterior probability density function which can be used to identify what model parameters are consistent with the observational data. The posterior is sampled using the Markov chain Monte Carlo (MCMC) method to give a discrete distribution of parameter values. 

BSAVI is a tool for exploratory analysis of this sample distribution of the posterior probability. Models with multiple parameters have high-dimensional posteriors, which makes them difficult to visualize. Additionally, it is often useful to see how a sample from the posterior (parameter space) translates into real-world observables (data space). To enable this, BSAVI has a built-in Observable class, which allows for easy annotation and plotting of each observable dataset. It can also take callables, so any preexisting code can be used with slight modifications to compute observables on the fly. BSAVI builds on the “holoviz” libraries, including “holoviews” and “panel”, with “Bokeh” as the interactive plotting backend.

# Statement of Need

BSAVI was originally developed for application in cosmology. In particular, developing dark matter models beyond cold, collisionless dark matter requires the use of Bayesian techniques in [@he2023selfinteracting] [reference Adam's and Trey's papers]. In this case, the theoretical model is one alternative to LambdaCDM, and the observables are the distribution of matter in the universe (given by the matter power spectrum) and the anisotropies in the cosmic microwave background (the CMB power spectrum). The Cosmic Linear Anisotropy Solving System (CLASS) is a code frequently used to generate these observables from input parameters [@Diego_blas_2011]. The parameters themselves are generated using Monte Python, a Markov Chain Monte Carlo sampler. The MCMC sampler generates values for each parameter in the model and runs them through CLASS to compare the output against observational data. It then continues to sample the parameter space with the goal of finding the region where the theoretical model best fits the observational evidence.

 The existing tools for visualizing the relationship between samples returned by MCMC and cosmological observables were separate and static, while a unified and interactive experience was desired. For example, a common method of visualizing the likelihood was to make pair plots of the parameters. A purpose-built package like corner is often used for this function. However, with high-dimensional likelihoods the number of pairs increases, and the resulting figure can become difficult to analyze. Additionally, corner and many other plotting tools use matplotlib as their backend, making it hard to interactively explore the dataset. There is a strong desire to see how a specific subset of the samples are distributed across the parameter space, as well as what their corresponding observables look like.

We solve this by providing researchers with an easy way to declare their observables, link them to a set of samples, and visualize them in an interactive dashboard. The user may supply their own function for BSAVI to dynamically compute observables, or a precomputed data table of the same length as their sample data. In the second case, the two tables will be linked by their indices.

# Example

Below is an example of using BSAVI to visualize a likelihood from the Planck 2018 Results:
[insert planck visualization from bsavi main page]
The code to generate this can be found on the [documentation page](https://wen-jams.github.io/bsavi/).
