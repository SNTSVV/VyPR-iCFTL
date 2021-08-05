![CI Status](https://gitlab.uni.lu/jdawes/VyPR-iCFTL/badges/master/pipeline.svg)

## VyPR for iCFTL

This repository contains implementations of instrumentation and monitoring for the iCFTL specification language.

iCFTL is an extension of CFTL to the inter-procedural setting.

### Authors

* Joshua Heneage Dawes (joshua.dawes@uni.lu)
* Domenico Bianculli (domenico.bianculli@uni.lu)


### Setting things up

To set up VyPR, you need to install the necessary Python libraries:
```
apt-get install graphviz
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements/main.txt
```
Depending on the OS, you may need to replace `apt-get` with your package manager (for example, `yum`).

### Running instrumentation

In order for VyPR to be able to monitor a program at runtime, the program needs to contain instrumentation code.

You can insert instrumentation code for a specification by running
```
python instrumentation_command_line.py --root-dir dir --spec-file spec-file.py
```
If you're using VyPR to analyse a Flask-based web service, you can add the `--flask` flag.  This will lead to the instrumentation code placed being modified to work with Flask.  For example, you could run
```
python instrumentation_command_line.py --root-dir dir --spec-file spec-file.py --flask
```

### Enabling monitoring

For the time being, we give instructions for activating monitoring in a web service.  You need to add the following code:
```
from VyPR.Monitoring.online import OnlineMonitor
vypr = OnlineMonitor("spec-file.py", flask_app)
```
where `flask_app` is the Flask application object.

### Running the tests

The set of unit tests can be run by navigating to `tests/` and running `python -m unittest`.

### Generating documentation

A script `generate-docs.sh` is provided in `docs/`, which uses `sphinx-apidoc` to automatically generate and builds Sphinx documentation based on the source code in the repository.

To run the script, make sure you're in `docs/`.  Once the script has finished, navigate to `docs/_build/html/index.html`.

## Licensing

VyPR for iCFTL is © 2021 University of Luxembourg and licensed under the the Apache 2 license.

Please read `VyPR-iCFTL licensing information.txt` for more details.
