"""
Module containing testing code for VyPR.Instrumentation.analyse module.
"""

import unittest
import ast
import sys
sys.path.append("..")

import VyPR.Logging.logger as logger

from VyPR.Instrumentation.analyse import Analyser
from VyPR.Specifications.builder import Specification
from VyPR.Specifications.predicates import changes, calls
from VyPR.SCFG.symbolic_states import StatementSymbolicState
from VyPR.SCFG.prepare import construct_scfg_of_function

class TestInstrumentationAnalyse(unittest.TestCase):

    def setUp(self):
        # initialise logger
        logger.initialise_logging(directory="../logs/test-logs/")
        # construct specification
        self.specification = Specification()\
            .forall(c = calls('f').during('test1.func1'))\
            .check(lambda c : c.duration() < 1)
        
        # read in module ASTs
        with open("test-data/programs/test1.py", "r") as h:
            code = h.read()
            module_asts = ast.parse(code)
        
        # construct function name -> scfg map
        function_name_to_scfg_map = {
            "test1.func1": construct_scfg_of_function("test1", module_asts, "test1.func1")
        }
        
        # initialise Analyser instance
        self.analyser = Analyser(self.specification, function_name_to_scfg_map)
    
    def tearDown(self):
        # close logging
        logger.end_logging()
    
    def test_inspect_quantifiers(self):
        # get the list of maps from variables to symbolic states
        maps = self.analyser._inspect_quantifiers()
        # assertions
        for map in maps:
            self.assertListEqual(list(map.keys()), ['c'])
            for variable in map:
                self.assertIsInstance(map[variable], StatementSymbolicState)
    
    def test_inspect_constraints(self):
        # construct variable -> symbolic state maps
        variable_to_symbolic_state_maps = self.analyser._inspect_quantifiers()
        # get the map map_index -> atomic_constraint_index -> subatom_index -> list of symbolic states.
        instrumentation_point_tree = self.analyser._inspect_constraints(variable_to_symbolic_state_maps)
        # assertions
        for map_index in instrumentation_point_tree:
            for symbolic_state in instrumentation_point_tree[map_index][0][0]:
                self.assertEqual(symbolic_state.get_symbols_changed(), ['f'])