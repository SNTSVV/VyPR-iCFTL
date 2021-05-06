"""
Module containing tests for the VyPR.SCFG.builder module.
"""

import unittest
import ast
import sys
sys.path.append("..")

import VyPR.Logging.logger as logger

from VyPR.SCFG.builder import SCFG
from VyPR.SCFG.search import SCFGSearcher
from VyPR.Specifications.predicates import calls, changes
from VyPR.Specifications.constraints import ConcreteStateVariable

class TestSCFGBuilder(unittest.TestCase):

    def setUp(self):
        # initialise logger
        logger.initialise_logging(directory="../logs/test-logs/")
        # read code and parse asts
        with open("test-data/programs/no-procedures-test-1.py") as h:
            self.code = h.read()
            self.asts = ast.parse(self.code).body
        # build scfg
        self.scfg = SCFG(self.asts)
        # get root symbolic state
        self.root_symbolic_state = self.scfg.get_root_symbolic_state()
    
    def tearDown(self):
        # close logging
        logger.end_logging()
    
    def test_get_symbolic_states_from_symbol(self):
        # get symbolic states
        symbolic_states = self.scfg.get_symbolic_states_from_symbol('f1')
        # assertions
        for symbolic_state in symbolic_states:
            self.assertListEqual(symbolic_state.get_symbols_changed(), ['f1'])
    
    def test_get_reachable_symbolic_states_from_symbol(self):
        # get symbolic states
        symbolic_states = self.scfg.get_reachable_symbolic_states_from_symbol('f1', self.root_symbolic_state)
        # assertions
        for symbolic_state in symbolic_states:
            self.assertListEqual(symbolic_state.get_symbols_changed(), ['f1'])
    
    def test_get_next_symbolic_states(self):
        # get next symbolic states
        symbolic_states = self.scfg.get_next_symbolic_states('f1', self.root_symbolic_state)
        # assertions
        for symbolic_state in symbolic_states:
            self.assertListEqual(symbolic_state.get_symbols_changed(), ['f1'])