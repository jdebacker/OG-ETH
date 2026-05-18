# OG-ETH

| | |
| --- | --- |
| Org | [![United Nations DESA](https://img.shields.io/badge/United%20Nations%20DESA-blue)](https://www.un.org/en/desa) [![PSL cataloged](https://img.shields.io/badge/PSL-cataloged-a0a0a0.svg)](https://www.PSLmodels.org) [![OS License: CC0-1.0](https://img.shields.io/badge/OS%20License-CC0%201.0-yellow)](https://github.com/EAPD-DRB/OG-ETH/blob/main/LICENSE) [![Jupyter Book Badge](https://raw.githubusercontent.com/jupyter-book/jupyter-book/next/docs/media/images/badge.svg)](https://eapd-drb.github.io/OG-ETH) |
| Package | [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3129/) [![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3137/) [![PyPI Latest Release](https://img.shields.io/pypi/v/ogeth.svg)](https://pypi.org/project/ogeth/) [![PyPI Downloads](https://img.shields.io/pypi/dm/ogeth.svg?label=PyPI%20downloads)](https://pypi.org/project/ogeth/) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) |
| Testing | ![example event parameter](https://github.com/EAPD-DRB/OG-ETH/actions/workflows/build_and_test.yml/badge.svg?branch=main) ![example event parameter](https://github.com/EAPD-DRB/OG-ETH/actions/workflows/deploy_docs.yml/badge.svg?branch=main) ![example event parameter](https://github.com/EAPD-DRB/OG-ETH/actions/workflows/check_ruff.yml/badge.svg?branch=main) [![Codecov](https://codecov.io/gh/EAPD-DRB/OG-ETH/branch/main/graph/badge.svg)](https://codecov.io/gh/EAPD-DRB/OG-ETH) |

OG-ETH is an overlapping-generations (OG) model that allows for dynamic general equilibrium analysis of fiscal policy for Ethiopia. OG-ETH is built on the OG-Core framework. The model output includes changes in macroeconomic aggregates (GDP, investment, consumption), wages, interest rates, and the stream of tax revenues over time. Regularly updated documentation of the model theory--its output, and solution method--and the Python API is available at https://pslmodels.github.io/OG-Core and documentation of the specific Ethiopian calibration of the model is available at https://eapd-drb.github.io/OG-ETH.


## Using and contributing to OG-ETH

There are two primary methods for installing and running OG-ETH on your computer locally. The first and simplest method is to download the most recent `ogeth` Python package from the Python Package Index ([PyPI.org](https://pypi.org/project/ogeth/)). The second option is to fork and clone the most recent version of OG-ETH from its GitHub repository and install the `ogeth` package with its development dependencies using `uv`. Both methods are detailed below.

### Installing and Running OG-ETH from PyPI

* On macOS, first install Xcode Command Line Tools (in Terminal: `xcode-select --install`).
* Open your terminal and install the [`ogeth`](https://pypi.org/project/ogeth/) package from the Python Package Index by typing `pip install ogeth`.
* Navigate to a folder `./YourFolderName/` where you want to save scripts to run OG-ETH and output from the simulations in those scripts.
* Copy the python script [`run_og_eth.py`](https://github.com/EAPD-DRB/OG-ETH/blob/main/examples/run_og_eth.py) from the OG-ETH GitHub repository into your folder as `./YourFolderName/run_og_eth.py`.
* Run the model with an example reform from terminal/command prompt by typing `python run_og_eth.py`.

### Installing and Running OG-ETH from the GitHub repository

* On macOS, first install Xcode Command Line Tools (in Terminal: `xcode-select --install`).
* Install [`uv`](https://docs.astral.sh/uv/) by following the [installation instructions](https://docs.astral.sh/uv/getting-started/installation/) for your platform (or simply run `pip install uv`).
* Fork this repository and clone your fork to a directory on your computer.
* From the terminal, navigate to the cloned directory and run `uv sync --extra dev` to create a local `.venv` and install OG-ETH with its development dependencies. `uv` will also download a compatible Python interpreter if you don't already have one.
* For docs/Jupyter Book work, also run `uv sync --extra dev --extra docs`.

### Run an example of the model

* Navigate to `./examples`.
* Run the model with an example reform: `uv run python run_og_eth.py` (or activate the venv first with `source .venv/bin/activate` on macOS/Linux or `.\.venv\Scripts\Activate.ps1` on Windows, then `python run_og_eth.py`).
* You can adjust the `./examples/run_og_eth.py` by modifying model parameters specified in the dictionary passed to the `p.update_specifications()` calls.
* Model outputs will be saved in the following files:
  * `./examples/OG-ETH_example_plots`
    * This folder will contain a number of plots generated from OG-Core to help you visualize the output from your run
  * `./examples/ogeth_example_output.csv`
    * This is a summary of the percentage changes in macro variables over the first ten years and in the steady-state.
  * `./examples/OG-ETH-Example/OUTPUT_BASELINE/model_params.pkl`
    * Model parameters used in the baseline run
    * See [`ogcore.execute.py`](https://github.com/PSLmodels/OG-Core/blob/master/ogcore/execute.py) for items in the dictionary object in this pickle file
  * `./examples/OG-ETH-Example/OUTPUT_BASELINE/SS/SS_vars.pkl`
    * Outputs from the model steady state solution under the baseline policy
    * See [`ogcore.SS.py`](https://github.com/PSLmodels/OG-Core/blob/master/ogcore/SS.py) for what is in the dictionary object in this pickle file
  * `./examples/OG-ETH-Example/OUTPUT_BASELINE/TPI/TPI_vars.pkl`
    * Outputs from the model timepath solution under the baseline policy
    * See [`ogcore.TPI.py`](https://github.com/PSLmodels/OG-Core/blob/master/ogcore/TPI.py) for what is in the dictionary object in this pickle file
  * An analogous set of files in the `./examples/OUTPUT_REFORM` directory, which represent objects from the simulation of the reform policy

Note that, depending on your machine, a full model run (solving for the full time path equilibrium for the baseline and reform policies) can take from 35 minutes to more than two hours of compute time.

If you run into errors running the example script, please open a new issue in the OG-ETH repo with a description of the issue and any relevant tracebacks you receive.

Once the package is installed, one can adjust parameters in the OG-Core `Specifications` object using the `Calibration` class as follows:

```
from ogcore.parameters import Specifications
from ogeth.calibrate import Calibration
p = Specifications()
c = Calibration(p)
updated_params = c.get_dict()
p.update_specifications({'initial_debt_ratio': updated_params['initial_debt_ratio']})
```

## Disclaimer
The organization of this repository will be changing rapidly, but the `OG-ETH/examples/run_og_eth.py` script will be kept up to date to run with the `main` branch of this repo.

## Core Maintainers

The core maintainers of the OG-ETH repository are:

* Marcelo LaFleur (GitHub handle: [@SeaCelo](https://github.com/SeaCelo)), Senior Economist, Department of Economic and Social Affairs (DESA), United Nations
* [Richard W. Evans](https://sites.google.com/site/rickecon/) (GitHub handle: [@rickecon](https://github.com/rickecon)), Senior Economist, Abundance Institute; President, Open Research Group, Inc.
* [Jason DeBacker](https://jasondebacker.com) (GitHub handle: [@jdebacker](https://github.com/jdebacker)), Associate Professor, University of South Carolina; Vice President of Research, Open Research Group, Inc.

## Citing OG-ETH

OG-ETH (Version #.#.#)[Source code], https://github.com/EAPD-DRB/OG-ETH.
