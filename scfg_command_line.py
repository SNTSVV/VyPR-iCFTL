"""
Command line module for generating a symbolic control-flow graph from a given Python 3 program.
"""

import ast
import argparse

from SCFG.builder import SCFG

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

# instantiate the scfg
scfg = SCFG(ast_list)

# write the scfg to a dot file
scfg.write_to_file(args.graph_file)