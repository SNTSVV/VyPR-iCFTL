"""
Module containing testing code for VyPR.Specifications.predicates module.
"""

import unittest

from VyPR.Specifications.predicates import changes, calls, future

class TestSpecificationsPredicates(unittest.TestCase):

    def setUp(self):
        self.incomplete_changes_predicate = changes('string')
        self.incomplete_calls_predicate = calls('f1')
        self.predicate_changes = changes('string').during('function')
        self.predicate_calls = calls('f1').during('function')
        self.predicate_future_changes = future(self.predicate_changes)
        self.predicate_future_calls = future(self.predicate_calls)
    
    def test_during_changes_predicate(self):
        self.assertEqual(self.predicate_changes.get_program_variable(), 'string')
    
    def test_during_calls_predicate(self):
        self.assertEqual(self.predicate_calls.get_function_name(), 'f1')
    
    def test_changes_completion(self):
        # complete instantiation of incomplete predicate
        complete_changes_predicate = self.incomplete_changes_predicate.during('function')
        self.assertIsInstance(complete_changes_predicate, changes)
    
    def test_calls_completion(self):
        # complete instantiation of incomplete predicate
        complete_calls_predicate = self.incomplete_calls_predicate.during('function')
        self.assertIsInstance(complete_calls_predicate, calls)
    
    def test_future_changes(self):
        self.assertIsInstance(self.predicate_future_changes.get_predicate(), changes)
    
    def test_future_calls(self):
        self.assertIsInstance(self.predicate_future_calls.get_predicate(), calls)