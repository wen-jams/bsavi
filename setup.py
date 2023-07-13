import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "inviz",
    version = "0.2.3",
    author = "James Wen",
    author_email = "jswen@usc.edu",
    description = ("An interactive visualizer to help explore high-dimensional data and its observables."),
    license = "MIT",
    keywords = "interactive visualizer cosmology",
    url = "http://packages.python.org/inviz",
    py_modules=["inviz"],
    package_dir={'': 'inviz'},
#    packages=['inviz'],
    #package_dir={'': 'inviz'},
    #long_description=long_description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.8',
    install_requires=["holoviews==1.15.4",
                      "panel==0.14.4",
                      "spatialpandas==0.4.7",
                      "param==1.13.0",
                      "numpy>=1.20, <1.24",
                      "matplotlib==3.7.1"]
    )

