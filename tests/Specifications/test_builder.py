"""
Module containing testing code for VyPR.Specifications.builder module.
"""

import unittest

from VyPR.Specifications.builder import Specification, timeBetween
from VyPR.Specifications.predicates import changes, calls, future
from VyPR.Specifications.constraints import ConcreteStateVariable, TransitionVariable

"""
Note: we define a test class for a single specification, so methods
defined on a single class perform tests on the single specification held.
"""

class TestSpecificationsBuilderSingleQuantifier(unittest.TestCase):

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

class TestSpecificationsBuilderTwoQuantifiers(unittest.TestCase):

    def setUp(self):
        # construct specification
        self.specification = Specification()\
            .forall(q = changes('string').during('function1'))\
            .forall(t = future(calls('f').during('function2')))\
            .check(lambda q, t : timeBetween(q, t.before()) < 1)
    
    def test_get_variables(self):
        self.assertListEqual(self.specification.get_variables(), ['q', 't'])
    
    def test_get_function_names_used(self):
        function_names_used = self.specification.get_function_names_used()
        self.assertSetEqual(set(function_names_used), set(['function1', 'function2']))
    
    def test_forall_structure(self):
        # get the quantifiers
        quantifiers = self.specification.get_variable_to_obj_map()
        # check the structure generated by the quantifiers
        # check the first quantifier
        self.assertIsInstance(quantifiers['q'], ConcreteStateVariable)
        # check the second quantifier
        self.assertIsInstance(quantifiers['t'], TransitionVariable)

class TestSpecificationsBuilderDuration(unittest.TestCase):

    def setUp(self):
        # construct specification
        self.specification = Specification()\
            .forall(c = calls('func').during('function1'))\
            .check(lambda c : c.duration() < 1)
    
    def test_get_variables(self):
        self.assertListEqual(self.specification.get_variables(), ['c'])
    
    def test_get_function_names_used(self):
        function_names_used = self.specification.get_function_names_used()
        self.assertListEqual(function_names_used, ['function1'])
    
    def test_forall_structure(self):
        # get the quantifiers
        quantifiers = self.specification.get_variable_to_obj_map()
        # check the type
        self.assertIsInstance(quantifiers['c'], TransitionVariable)