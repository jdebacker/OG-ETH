# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.8] - 2026-05-18 23:00:00

### Added
* Reads the SAM file from `ogeth/data/` instead of fetching it from GitHub at runtime, so offline runs work
* Adds a `pip-import-smoke` CI job that installs the package and imports it from a temp directory, catching packaging issues invisible from the source tree

### Fixed
* Fixes `alpha_c` to sum only the ten household columns of the SAM (instead of total - row, which included government, investment, and intermediate use), matching OG-IDN and OG-PHL

## [0.0.7] - 2026-05-12 00:50:00

### Fixed

- Fixed bug in `calibrate.py` where the `income.get_e_interp` function was not being called with the correct parameters. This was causing an error when running the `calibrate.py` script.

## [0.0.6] - 2026-04-15 15:50:00

### Added

- Updates connections to API calls to the World Bank, IMF, and UN in `macro_params.py` and `calibrate.py` to allow for updating the exogenous parameters from the APIs. This is currently set to `False` by default, but can be set to `True` to update the parameters from the APIs when running the `calibrate.py` script. The documentation in `exogenous_parameters.md` has also been updated to reflect this change.
- Updates how the SAM file is loaded in `input_output.py`
- Adds an `update_baseline.py` script that updates the default parameters in `ogeth_default_parameters.json` based on the output of the `calibrate.py` script. This allows us to easily update the default parameters in the JSON file when we run the calibration script.

## [0.0.5] - 2025-11-17 23:40:00

### Added

- Updates average household income `mean_income_data` to ETB 157,845 and the corresponding documentation in `matching_lwi.md`
- Updates initial debt-to-GDP and the corresponding documentation in `macro.md`

## [0.0.4] - 2025-11-17 18:30:00

### Added

- Updates the TPI resource constraint `RC_TPI=0.01`

## [0.0.3] - 2025-11-17 13:00:00

### Added

- Updates default parameters

## [0.0.2] - 2025-11-16 13:00:00

### Added

- Fixes black formatting in `income.py` and `input_output.py`
- Fixes a typo in `constants.py`
- Fixes an error in the `deploy_docs.yml` and `docs_check.yml` files
- Adds Jason as a core maintainer in `intro.md`. This also allows us to see if the documentation GH Actions work.
- Removed `test_income.py` and `test_input_output.py` tests

## [0.0.1] - 2025-11-16 12:30:00

### Added

- Adds 3 logo files to the `./docs/` directory: `OG-ETH_logo_gitfig.png`, `OG-ETH_logo_long.png`, and `OG-ETH_logo.png`.
- Updates a `.gitignore` file.
- Fixes references in `./docs/book/content/OGETH_references.md`, `./docs/create_doc_figures.py`, `PSL_catalog.json,` and `./docs/README.md`
- Fixes badges in `README.md` and `intro.md`
- Pins the `environment.yml` package `jupyter-book<2.0.0` so that the book can build with `jb build ...` command.
- Updates the functions in `input_output.rst` and `utils.rst`
- Updates the Jupyter metadata in `earnings.md` and `exogenous_parameters.md`. This is what was stopping the Jupyter Book from compiling (once we pinned `jupyter-book<2.0.0`).
- Adds GH Action files `build_and_tes.yml`, `check_format.yml`, `deploy_docs.yml`, `docs_check.yml`, `publish_to_pypi.yml`, `ISSUE_TEMPLATE.md`, and `PULL_REQUEST_TEMPLATE.md`. These files required me to add OG-ETH to Codecov.io, add a repository secret for Codecov, create the gh-pages branch with the files for the Jupyter Book and publish it as a GitHub pages site, create and upload the first version of the `ogeth` package to PyPI.org, and add a repository secret for PYPI.

## [0.0.0] - 2025-10-06 12:00:00

### Added

- This version is a pre-release alpha. The example run script OG-ETH/examples/run_og_eth.py runs, but the model is not currently calibrated to represent the Ethiopian economy and population.


[0.0.8]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.7...v0.0.8
[0.0.7]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.6...v0.0.7
[0.0.6]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.5...v0.0.6
[0.0.5]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.0...v0.0.1
