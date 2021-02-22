"""
Command line module for generating a symbolic control-flow graph from a given Python 3 program.
"""

import ast
import os
import argparse

from SCFG.module_processor import ModuleProcessor

# define command line arguments
parser = argparse.ArgumentParser(description="Command line interface for SCFG construction package.")
parser.add_argument("--source-file", type=str, required=True, help="The file containing the code for which we will generate SCFGs.")
parser.add_argument("--graph-file", type=str, required=True, help="The line number of the log entry from which to perform slicing.")

# parse the arguments
args = parser.parse_args()

# read the source code from the given source file
with open(args.source_file, "r") as h:
    code = h.read()
    ast_list = ast.parse(code).body

# derive the module name by removing .py from the file name
# and removing directories
module_name = os.path.abspath(args.source_file).split("/")[-1].replace(".py", "")

# get a ModuleProcessor instance
module_processor = ModuleProcessor(module_name, ast_list)

# get a map from fully-qualified function names in the module to their SCFGs
function_name_to_scfg = module_processor.get_name_to_scfg_map()

# write scfgs to file
for function_name in function_name_to_scfg:
    function_name_to_scfg[function_name].write_to_file(f"scfgs/{function_name}.gv")