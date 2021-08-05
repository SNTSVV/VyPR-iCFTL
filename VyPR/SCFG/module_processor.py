"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module containing the logic to find function/method definitions in a given Python 3
module and construct a map from fully-qualified names to SCFGs.
"""

import ast

from VyPR.SCFG.builder import SCFG

class ModuleProcessor():

    def __init__(self, module_name: str, module_asts: list):
        """
        Given a list of asts for a Python module,
        store them ready for construction of a map from fully-qualified function
        names to SCFGs.
        """
        self._module_name = module_name
        self._module_asts = module_asts
    
    def get_name_to_scfg_map(self) -> dict:
        """
        Process self._module_asts in order to construct a map from
        fully-qualified names to SCFG instances.

        To do this, we walk each ast in the list
        until we find ast.FunctionDef instances, at which point we
        construct the SCFG of the function and add it to the map.
        """
        # initialise empty map
        name_to_scfg = {}
        # walk each ast
        for block_ast in self._module_asts:
            for walked_ast in ast.walk(block_ast):
                if type(walked_ast) is ast.FunctionDef:
                    # get the fully-qualified version
                    fully_qualified_function_name = f"{self._module_name}.{walked_ast.name}"
                    # add to the map
                    name_to_scfg[fully_qualified_function_name] = SCFG(walked_ast.body)
        
        return name_to_scfg