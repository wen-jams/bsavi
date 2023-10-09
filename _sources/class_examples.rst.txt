Cosmology & CLASS
==================

The `CLASS code <https://lesgourg.github.io/class_public/class.html>`_ is widely used
by cosmologists to simulate the evolution of linear perturbations in the universe and
to compute CMB and large scale structure observables. CLASS accepts cosmological parameters 
as input, which we will get from the Planck 2018 results. The following code demonstrates 
using InViz to visualize the Planck 2018 results in parameter space and their relationship 
with three observables: the matter power spectrum :math:`P(k)`, and the power spectra of 
the CMB temperature :math:`C_{l}^{TT}` and polarization :math:`C_{l}^{EE}`.

We will look at Table 6.7 from the 
`Planck 2018 table of parameters <https://wiki.cosmos.esa.int/planck-legacy-archive/images/4/43/Baseline_params_table_2018_68pc_v2.pdf>`_.
The data required for this tutorial is located 
`here: <https://github.com/wen-jams/inviz/tree/main/data/planck2018/plikHM_TTTEEE_lowl_lowE_lensing>`_.


Pre-Computed Observables
------------------------

Let's start with the case of pre-computed observables. A small sample was taken from the chains
and run through CLASS. The results, along with the samples themselves, are in ``power_spectra_small.json``.

Begin by loading the data file and splitting it into chains and spectra:

.. code-block:: python

    planck = pd.read_json('data/planck2018/plikHM_TTTEEE_lowl_lowE_lensing/power_spectra_small.json')
    chains = planck.drop(columns=['p(k)', 'cl_tt', 'cl_ee'])
    class_results = planck[['p(k)', 'cl_tt', 'cl_ee']]

Read in the ``.paramnames`` file that was included with the data. This is a list of each parameter and the corresponding 
LaTeX code. We will make a dictionary of these labels which will be used later.

.. code-block:: python

    from inviz.cosmo import load_params

    param_names, latex_params = load_params('../data/planck2018/plikHM_TTTEEE_lowl_lowE_lensing/base_mnu_plikHM_TTTEEE_lowl_lowE_lensing.paramnames')
    params_latex_form = dict(zip(param_names, latex_params))

Now we are ready to construct an Observable which combines the observable data with plotting instructions.

.. code-block:: python

    import inviz as iv
    from holoviews import opts

    curve_opts = opts.Curve(logx=True)

    ps_latex = {
        'k': 'k~[h/\mathrm{Mpc}]',
        'Pk': 'P(k)',
        'l': '\ell',
        'Cl_tt': '[{\ell(\ell+1)}/{2\pi}]~C_{\ell}^{TT}',
        'Cl_ee': '[{\ell(\ell+1)}/{2\pi}]~C_{\ell}^{EE}',
    }

    power_spectra = iv.Observable(
        name=['P(k)', 'Lensed Cl_TT', 'Lensed Cl_EE'], 
        parameters=class_results,
        plot_type='Curve',
        plot_opts=curve_opts,
    )

Finally, produce the visualization with:

.. code-block:: python

    iv.viz(data=chains, observables=[power_spectra], latex_dict=params_latex_form).servable()


Dynamically Computed Observables
--------------------------------

