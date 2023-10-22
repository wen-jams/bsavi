.. InViz documentation master file, created by
   sphinx-quickstart on Fri Sep 29 21:13:50 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to InViz's documentation!
=================================

InViz (Interactive Visualizer) is a tool to aid likelihood analysis of model parameters where samples 
from a distribution in the parameter space are used as inputs to calculate a given observable. 
For example, selecting a range of samples will allow you to easily see how the observables change 
as you traverse the sample distribution. At the core of InViz is the `Observable` object, which contains 
the data for a given observable and instructions for plotting it. It is modular, so you can write your 
own function that takes the parameter values as inputs, and InViz will use it to compute observables 
on the fly. It also accepts tabular data, so if you have pre-computed observables, simply import them 
alongside the dataset containing the sample distribution to start visualizing!

Check out the :doc:`usage` section for further information, including how to :ref:`install <installation>` the project.

See :doc:`quickstart` for a brief introduction to the code. :doc:`class_examples` has examples for how cosmologists 
might use InViz, and for an in-depth walkthrough of InViz and all of its features, see :doc:`userguide`.

.. note::

   This project is under active development.

Contents
--------
.. toctree::
   :maxdepth: 2

   usage
   quickstart
   class_examples
   userguide
   reference