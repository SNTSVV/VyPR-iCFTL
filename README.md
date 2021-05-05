![CI Status](https://gitlab.uni.lu/jdawes/VyPR-iCFTL/badges/master/pipeline.svg)

## VyPR for iCFTL

This repository contains implementations of instrumentation and monitoring for the iCFTL specification language.

iCFTL is an extension of CFTL to the inter-procedural setting.

### Running the tests

The set of unit tests can be run by navigating to `tests/` and running `python -m unittest`.

### Generating documentation

A script `generate-docs.sh` is provided in `docs/`, which uses `sphinx-apidoc` to automatically generate and builds Sphinx documentation based on the source code in the repository.

To run the script, make sure you're in `docs/`.  Once the script has finished, navigate to `docs/_build/html/index.html`.