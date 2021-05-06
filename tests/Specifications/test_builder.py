"""
Module containing testing code for VyPR.Specifications.builder module.
"""

import unittest

from VyPR.Specifications.builder import Specification
from VyPR.Specifications.predicates import changes, calls

class TestSpecificationsBuilder(unittest.TestCase):

    def setUp(self):
        # construct specification
        self.specification = Specification()\
            .forall(q = changes('string').during('function'))\
            .check(lambda q : q.next(calls('f1').during('function')).duration() < 1)
    
    def test_get_variable_to_obj_map(self):
        variables = list(self.specification.get_variable_to_obj_map().keys())
        self.assertListEqual(variables, ['q'])
    
    def test_get_variables(self):
        self.assertListEqual(self.specification.get_variables(), ['q'])
    
    def test_get_function_names_used(self):
        function_names_used = self.specification.get_function_names_used()
        self.assertListEqual(function_names_used, ['function'])
    
    def test_forall_structure(self):
        # get the single quantifier from the specification
        # since there is only one, we don't need to recurse on the structure
        quantifier = self.specification.get_quantifier()
        # assert on the name of the variable and the type of the predicate used
        self.assertEqual(quantifier.get_variable(), 'q')
        self.assertIsInstance(quantifier.get_predicate(), changes)
    
    