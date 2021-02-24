"""
Command line module for generating a symbolic control-flow graph from a given Python 3 program.
"""

import ast
import os
import argparse

from VyPR.SCFG.module_processor import ModuleProcessor

# initialise logging
import VyPR.Logging.logger as logger
logger.initialise_logging(directory="logs/scfg/")

# define command line arguments
parser = argparse.ArgumentParser(description="Command line interface for SCFG construction package.")
parser.add_argument("--source-file", type=str, required=True, action="append", help="The file containing the code for which we will generate SCFGs.")

# parse the arguments
args = parser.parse_args()

# process each source file given
for filename in args.source_file:
    # read the source code from the given source file
    with open(filename, "r") as h:
        code = h.read()
        ast_list = ast.parse(code).body
        
    # derive the module name by removing .py from the file name
    # and removing directories
    module_name = os.path.abspath(filename).split("/")[-1].replace(".py", "")

    # get a ModuleProcessor instance
    module_processor = ModuleProcessor(module_name, ast_list)

    # get a map from fully-qualified function names in the module to their SCFGs
    function_name_to_scfg = module_processor.get_name_to_scfg_map()

    # write scfgs to file
    for function_name in function_name_to_scfg:
        scfg_file = f"scfgs/{function_name}.gv"
        function_name_to_scfg[function_name].write_to_file(scfg_file)
        print(f"SCFG for function '{function_name}' written to file '{scfg_file}.pdf'")

# close logging
logger.log.close()