# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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


[0.0.5]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/EAPD-DRB/OG-ETH/compare/v0.0.0...v0.0.1
