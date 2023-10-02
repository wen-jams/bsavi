Library Reference
=================

.. py:class:: inviz.Observable(name, parameters=None, latex_labels=None, myfunc=None, myfunc_args=None, plot_type, plot_opts=None)

    .. py:attribute:: name

        Specifies the display name of the observable for things like plot titles.

        :type: str or list[str]
    
    .. py:attribute:: parameters

        The data to associated with that observable. Can be python dict (or pandas DataFrame)
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
        that connects data points together or 'Scatter' for a simple scatter plot.

        :type: str
        
    .. py:attribute:: plot_opts

        Customization options for the observable plot. For more information
        see `HoloViews documentation <https://holoviews.org/user_guide/Applying_Customizations.html>`_.

        :type: HoloViews Options object
        
        :value: None

.. py:function:: inviz.viz(data, observables=None, show_observables=False, latex_dict=None)

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
