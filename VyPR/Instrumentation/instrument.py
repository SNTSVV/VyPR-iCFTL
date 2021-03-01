"""
Module containing the logic for adding instrumentation code based on the results of static analysis with respect to iCFTL specifications.
"""

import ast

from VyPR.Instrumentation.analyse import Analyser

class Instrument():
    """
    Class used to invoke Analyser in order to perform static analysis,
    modify the ASTs of files to be instrumented and perform the final compilation.
    """

    def __init__(self, specification_file: str, root_directory: str):
        """
        Invoke analyser with the specification file and root directory given.
        """
        # instantiate the analyser
        self._analyser = Analyser(specification_file, root_directory)
        # store the map from function names to ast lists
        self.function_name_to_ast_list_map = self._analyser.get_function_to_ast_list_map()
        # compute the instrumentation tree
        self._instrumentation_tree = self._analyser.compute_instrumentation_points()
    
    def insert_instruments(self):
        """
        Traverse the instrumentation tree structure and, for each symbolic state,
        place an instrument at an appropriate position around the AST provided by the symbolic state.
        """
        # traverse self._instrumentation_tree
        for map_index in self._instrumentation_tree:
            for atom_index in self._instrumentation_tree[map_index]:
                for subatom_index in self._instrumentation_tree[map_index][atom_index]:
                    # iterate through the symbolic states
                    for symbolic_state in self._instrumentation_tree[map_index][atom_index][subatom_index]:
                        insertion_block = symbolic_state.get_ast_object().parent_block
                        index_in_block = symbolic_state.get_ast_object().parent_block.index(symbolic_state.get_ast_object())
                        # generate the instrument's ast
                        instrument_ast = self.generate_instrument_ast(map_index, atom_index, subatom_index)
                        # insert the ast
                        insertion_block.insert(index_in_block, instrument_ast)
    
    def generate_instrument_ast(self, map_index: int, atom_index: int, subatom_index: int) -> str:
        """
        Given the map, atom and subatom indices, generate the code to insert.
        """
        # define code template
        # TODO: make function the instrument calls a parameter
        code = f"""
print(f"map index = {map_index}, atom index = {atom_index}, subatom index = {subatom_index}")
        """
        # generate an ast
        code_ast = ast.parse(code)
        # get the statement ast
        statement_ast = code_ast.body[0]
        return statement_ast