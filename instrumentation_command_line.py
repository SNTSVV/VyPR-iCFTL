"""
Module for command line interface with the Instrumentation package.
"""

import ast
import os
import argparse
import pprint

from VyPR.Specifications.builder import Specification, all_are_true, one_is_true, not_true, timeBetween
from VyPR.Specifications.predicates import changes, calls, future
from VyPR.SCFG.module_processor import ModuleProcessor
from VyPR.SCFG.prepare import construct_scfg_of_function
from VyPR.Instrumentation.analyse import Analyser
from VyPR.Instrumentation.prepare import prepare_specification
from VyPR.Instrumentation.instrument import Instrument

# initialise logging
import VyPR.Logging.logger as logger
logger.initialise_logging(directory="logs/instrumentation/")

# define command line arguments
parser = argparse.ArgumentParser(description="Command line interface for the instrumentation package.")
parser.add_argument("--root-dir", type=str, required=True, help="The directory containing the code for which we will generate SCFGs.")
parser.add_argument("--spec-file", type=str, required=True, help="The file containing the code for the specification that we should instrument for.")

# parse the arguments
args = parser.parse_args()

# initialise Instrument object
instrument_instance = Instrument(args.spec_file, args.root_dir)

# insert instruments
instrument_instance.insert_instruments()

# close logging
logger.log.close()