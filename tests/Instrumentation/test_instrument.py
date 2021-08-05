"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module containing testing code for VyPR.Instrumentation.analyse module.
"""

import unittest
import ast
import sys
sys.path.append("..")

import VyPR.Logging.logger as logger

from VyPR.Instrumentation.instrument import Instrument
from VyPR.Specifications.builder import Specification
from VyPR.Specifications.predicates import changes, calls
from VyPR.SCFG.symbolic_states import StatementSymbolicState
from VyPR.SCFG.prepare import construct_scfg_of_function

class TestInstrumentationAnalyse(unittest.TestCase):

    def setUp(self):
        # initialise logger
        logger.initialise_logging(directory="../logs/test-logs/")
        # define specification file
        self.specification_file = "test-data/specifications/test3.py"
        
        # initialise Instrument instance
        self.instrument = Instrument(self.specification_file, "test-data/programs/", False)
    
    def tearDown(self):
        # close logging
        logger.end_logging()

    def test_derive_list_of_modules(self):
        # get list of modules
        modules = self.instrument._derive_list_of_modules()
        # assertions
        self.assertListEqual(modules, ['test1'])
    
    def test_get_module_from_function(self):
        # get module name from function name
        module_name = self.instrument._get_module_from_function("pkg.module.function")
        # assertions
        self.assertEqual(module_name, "pkg.module")
    
    def test_get_indentation_level_of_stmt(self):
        # get indentation level
        indentation_level = self.instrument.get_indentation_level_of_stmt("  a = 10")
        # assertions
        self.assertEqual(indentation_level, 2)
    
    def test_get_original_filename_from_module(self):
        # get original filename
        original_filename = self.instrument._get_original_filename_from_module("pkg1.pkg2.module")
        # assertions
        self.assertEqual(original_filename, "test-data/programs/pkg1/pkg2/module.py")
    
    def test_get_backup_filename_from_module(self):
        # get backup filename
        backup_filename = self.instrument._get_backup_filename_from_module("pkg1.pkg2.module")
        # assertions
        self.assertEqual(backup_filename, "test-data/programs/pkg1/pkg2/module_vypr_original.py")