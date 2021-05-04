"""
Module containing tests for the VyPR.SCFG.search module.
"""

import unittest
import ast
import sys
sys.path.append("..")

import VyPR.Logging.logger as logger

from VyPR.SCFG.builder import SCFG
from VyPR.SCFG.search import SCFGSearcher
from VyPR.Specifications.predicates import calls, changes

class TestSCFGSearch(unittest.TestCase):

    def setUp(self):
        # initialise logger
        logger.initialise_logging(directory="../logs/test-logs/instrumentation/")
        # read code and parse asts
        with open("test-data/programs/no-procedures-test-1.py") as h:
            self.code = h.read()
            self.asts = ast.parse(self.code).body
        # build scfg
        self.scfg = SCFG(self.asts)
        # get root symbolic state
        self.root_symbolic_state = self.scfg.get_root_symbolic_state()
        # build dictionary mapping function names to scfgs
        function_name_to_scfg_map = {
            "function": self.scfg
        }
        # instantiate SCFGSearcher instance
        self.scfg_searcher = SCFGSearcher(function_name_to_scfg_map)
    
    def tearDown(self):
        # close logging
        logger.end_logging()
    
    def test_find_symbolic_states_with_call(self):
        # define predicate
        predicate = calls('f1').during('function')
        # get symbolic state satisfying the predicate
        symbolic_states = self.scfg_searcher.find_symbolic_states(predicate, self.root_symbolic_state)
        # assertions
        for symbolic_state in symbolic_states:
            self.assertListEqual(symbolic_state.get_symbols_changed(), ["f1"])
    
    def test_find_symbolic_states_with_change(self):
        # define predicate
        predicate = changes('string').during('function')
        # get symbolic state satisfying the predicate
        symbolic_states = self.scfg_searcher.find_symbolic_states(predicate, self.root_symbolic_state)
        # assertions
        for symbolic_state in symbolic_states:
            self.assertListEqual(symbolic_state.get_symbols_changed(), ["string"])