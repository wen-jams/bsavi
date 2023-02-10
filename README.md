# inviz

This tool helps you visualize samples from the posterior distribution of your cosmological model. Selecting a point on the sample distribution will automatically run CLASS on that sample and display the output.

Right now, the entire visualizer is contained in the `visualizer.ipynb` file. In there, you will find detailed instructions on how to upload your data and run the code.

## Dependencies
You  will need Python $\ge$ 3.6 and pip.

You will also need CLASS installed (either from class_public or your own modified version). Follow the instructions [here](https://cobaya.readthedocs.io/en/latest/theory_class.html) to install `classy`, the Python wrapper for Class.
