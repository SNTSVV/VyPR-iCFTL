"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module containing tests for the VyPR.SCFG.utils module.
"""

import unittest
import ast
import sys
sys.path.append("..")

import VyPR.Logging.logger as logger

from VyPR.SCFG.symbolic_states import EmptySymbolicState, StatementSymbolicState
from VyPR.SCFG.utils import process_assignment_ast, process_expression_ast, extract_function_names, extract_symbol_names_from_target

class TestSCFGUtils(unittest.TestCase):

    def setUp(self):
        # initialise logger
        logger.initialise_logging(directory="../logs/test-logs/")
        # define assignment statement code
        self.assignment_stmt_code = "a = 10 + g()"
        # parse ast
        self.assignment_stmt_ast = ast.parse(self.assignment_stmt_code).body[0]
        # define expression statement code
        self.expression_stmt_code = "f()"
        # parse ast
        self.expression_stmt_ast = ast.parse(self.expression_stmt_code).body[0]
    
    def tearDown(self):
        # close logging
        logger.end_logging()
    
    def test_build_symbolic_state_for_assignment(self):
        # set up empty parent symbolic state
        parent_symbolic_state = EmptySymbolicState()
        # instantiate symbolic state for assignment
        assignment_symbolic_state = process_assignment_ast(self.assignment_stmt_ast, parent_symbolic_state)
        # assertions
        self.assertIsInstance(assignment_symbolic_state, StatementSymbolicState)
        self.assertListEqual(assignment_symbolic_state.get_symbols_changed(), ["a", "g"])
    
    def test_build_symbolic_state_for_expression(self):
        # set up empty parent symbolic state
        parent_symbolic_state = EmptySymbolicState()
        # instantiate symbolic state for expression
        expression_symbolic_state = process_expression_ast(self.expression_stmt_ast, parent_symbolic_state)
        # assertions
        self.assertIsInstance(expression_symbolic_state, StatementSymbolicState)
        self.assertListEqual(expression_symbolic_state.get_symbols_changed(), ["f"])
    
    def test_extract_variable_names(self):
        # extract the variable names from the right-hand-side of the assignment
        extracted_variable_names = extract_symbol_names_from_target(self.assignment_stmt_ast.value)
        # assertions
        self.assertListEqual(extracted_variable_names, ["g"])
    
    def test_extract_function_names(self):
        # extract the function names from the right-hand-side of the assignment
        extracted_function_names = extract_function_names(self.assignment_stmt_ast.value)
        # assertions
        self.assertListEqual(extracted_function_names, ["g"])