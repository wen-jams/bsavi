# inviz

This tool helps you explore the results of running MCMC posterior sampling on your cosmological model. Selecting a point on the sample distribution will automatically run CLASS on that sample and display the output.

Right now, the entire visualizer is contained in the `visualizer.ipynb` file. In there, you will find detailed instructions on how to upload your data and run the code.

## Dependencies
You  will need Python $\ge$ 3.6 and Conda.

You can either use the included `environment.yml` file to create a new Conda environment from the dependencies, or add them to an existing one. In your terminal, run

    conda env create -f environment.yml

to create a new environment, or

    conda activate myenv
    conda env update --name myenv --file environment.yml

to update your existing one.

You will also need CLASS installed (either from class_public or your own modified version). Follow the instructions [here](https://cobaya.readthedocs.io/en/latest/theory_class.html) to install classy, the Python wrapper for Class.

