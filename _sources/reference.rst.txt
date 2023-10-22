API Reference
=================

.. py:module:: inviz

.. py:class:: Observable(name, parameters=None, latex_labels=None, myfunc=None, myfunc_args=None, plot_type, plot_opts=None)

    .. py:attribute:: name

        Specifies the display name of the observable for things like plot titles.

        :type: str or list[str]
    
    .. py:attribute:: parameters

        The data associated with that observable. Can be python dict (or pandas DataFrame)
        whose keys (or column names) will be used for things like plot axis labels.

        :type: dict-like or list[dict-like]

        :value: None

    .. note:: 

        If providing values for ``Observable.parameters``, leave ``myfunc`` and ``myfunc_args``
        as None, and vice versa.

    .. py:attribute:: latex_labels

        A dictionary that has parameter labels as keys and their corresponding 
        LaTeX format as values.

        :type: dict or list[dict]

        :value: None

    .. py:attribute:: myfunc

        A user-provided function that returns parameters in the same data format
        that :py:attr:`Observable.parameters` accepts. Can return more than one
        set of parameters. See above note for usage with :py:attr:`Observable.parameters`.

        :type: Callable
        
        :value: None

    .. py:attribute:: myfunc_args

        Arguments for the user-provided function :py:attr:`Observable.myfunc`.

        :type: tuple
        
        :value: None

    .. py:attribute:: plot_type

        Specifies how the data should be visualized. Currently can pick either 'Curve'
        that connects data points together, 'Bars' for a series of columns with their 
        heights determined by the y-axis value at each point, or 'Scatter' for a simple 
        scatter plot.

        Pass a single value to set it for all datasets in the Observable, or a list of 
        values to be set for each dataset.

        :type: str or list[str]
        
    .. py:attribute:: plot_opts

        Customization options for the observable plot. For more information
        see `HoloViews documentation <https://holoviews.org/user_guide/Applying_Customizations.html>`_.

        :type: HoloViews Options object
        
        :value: None

    .. py:method:: properties()

        Prints information about the Observable.

    .. py:method:: generate_plot(index)

        Generates plots of the data at the given index. Will call :py:attr:`Observable.myfunc` with :py:attr:`Observable.myfunc_args`
        on the data if given. The plots are returned as a list of objects which can be manipulated as you wish.

        :param index: The index location of the data to plot
        :type index: int
        :returns: A list of `Holoviews Elements <https://holoviews.org/user_guide/Annotating_Data.html>`_

    .. py:method:: draw_plot(index)

        Displays an interactive plot of the data at the given index. Whereas :py:meth:`Observable.generate_plot` returns 
        a list of plot objects but does not display them, this method will display plots arranged in a layout when evaluated 
        in a Jupyter Notebook cell.

        :param index: The index location of the data to plot
        :type index: int
        :returns: A `layout of Holoviews Elements <https://holoviews.org/user_guide/Composing_Elements.html>`_

.. py:function:: viz(data, observables=None, show_observables=False, latex_dict=None)

    Displays an interactive dashboard that links ``data`` to ``observables``.

    :param data: The data or distribution to be visualized as a scatterplot
    :type data: dict-like
    :param observables: A list of the observables to be visualized
    :type observables: list[:py:class:`inviz.Observable`]
    :param show_observables: Whether to display the observable plots or not. Default behavior is: ``True`` if observables are given, ``False`` if not.
    :type show_observables: bool
    :param latex_dict: A dictionary containing the LaTeX formatting for the scatterplot axis labels
    :type latex_dict: dict
    :returns: A collection of `Panel <https://panel.holoviz.org/api/cheatsheet.html>`_ components 

.. py:module:: inviz.cosmo

.. py:function:: load_params(filename)

    Reads in a ``.paramnames`` file and returns a dict of each parameter's plain text and LaTeX name. 
    Assumes that the file is in the proper format: each line should contain one plain text param name and its LaTeX counterpart separated by 
    a ``tab`` character (``\t``). Any amount of whitespace on either side of the tab character is acceptable.

    :param filename: path to the ``.paramnames`` file
    :type filename: str
    :returns: a dict of parameter names and LaTeX code

.. py:function:: load_chains(path, params, params_only=True)

    Reads in a chain file and converts it to a `DataFrame <https://pandas.pydata.org/docs/reference/frame.html>`_. Assumes that the file 
    is a .txt file with the following columns: *weight, -LogLkl, param1, param2, ...*. 
    
    *Weight* is the number of iterations the MCMC sampler stayed at that parameter set (the sample weight) and 
    *-LogLkl* is the negative log of the likelihood. This is the standard format of both `CosmoMC <https://cosmologist.info/cosmomc/readme.html>`_ 
    and `Monte-Python <https://monte-python.readthedocs.io/en/latest/index.html>`_ chain files.

    :param path: name of the chain file, list of names, or glob pattern
    :type path: str, list['str']
    :param params: list of parameter names which will be used as column names for the DataFrame.
    :type params: list['str']
    :param params_only: whether to ignore the first two columns of the chain file (weight and -LogLKL).
        Default is True, which will disregard those columns when reading in the file.
    :type params_only: bool
    :returns: Pandas DataFrame

.. py:function:: run_class(index, sample)

    Calls the CLASS code on a given index of the sample data to calculate the matter power spectrum :math:`P(k)`, the lensed power spectrum of 
    the CMB temperature :math:`C_{l}^{TT}`, and the lensed power spectrum of the CMB polarization :math:`C_{l}^{EE}`.

    Uses the following settings:

    .. code-block:: python

        {'output':'mPk, tCl, pCl, lCl','P_k_max_1/Mpc':3.0, 'lensing':'yes'}

    :param index: index location of the sample to be run through CLASS
    :type index: int
    :param sample: a DataFrame where each row contains samples of cosmological parameters which CLASS accepts as inputs
    :type sample: Pandas DataFrame
    :returns: the three power spectra in the form of a dictionary where each key contains an array of wave numbers :math:`k` or 
        multipole moments :math:`\ell` and each value contains an array of the calculated values for each :math:`k` or :math:`\ell`.

.. py:function:: compute_residuals(index, sample, sample_CDM)

    Useful for exploring beyond-CDM cosmologies. Calls the CLASS code on two sets of sample data (one with beyond-CDM parameters, and 
    one with CDM parameters), at the specified index. Computes the percent difference in the three observables (:math:`P(k)`, 
    :math:`C_{l}^{TT}`, :math:`C_{l}^{EE}`) for each value of :math:`k` or :math:`\ell`.

    :param index: index location of the sample to be run through CLASS
    :type index: int
    :param sample: a DataFrame where each row contains samples of beyond-CDM cosmological parameters
    :type sample: Pandas DataFrame
    :param sample_CDM: a DataFrame where each row contains samples of LCDM cosmological parameters
    :type sample_CDM: Pandas DataFrame
    :returns: the power spectrum residuals in the same format as :py:func:`run_class`

