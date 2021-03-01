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
from VyPR.Instrumentation.instrument import Analyser
from VyPR.Instrumentation.prepare import prepare_specification

# initialise logging
import VyPR.Logging.logger as logger
logger.initialise_logging(directory="logs/instrumentation/")

# define command line arguments
parser = argparse.ArgumentParser(description="Command line interface for the instrumentation package.")
parser.add_argument("--root-dir", type=str, required=True, help="The directory containing the code for which we will generate SCFGs.")
parser.add_argument("--spec-file", type=str, required=True, help="The file containing the code for the specification that we should instrument for.")

# parse the arguments
args = parser.parse_args()

# initialise Analyser object
analyser = Analyser(args.spec_file, args.root_dir)

# compute instrumentation points
symbolic_states = analyser.compute_instrumentation_points()

pprint.pprint(symbolic_states)

# close logging
logger.log.close()