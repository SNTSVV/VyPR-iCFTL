"""
Module containing testing code for VyPR.Specifications.builder module.
"""

import unittest

from VyPR.Specifications.builder import Specification, timeBetween, all_are_true
from VyPR.Specifications.constraints import (ConcreteStateVariable,
                                            _is_constraint_base,
                                            is_complete,
                                            _is_connective,
                                            is_normal_atom,
                                            is_mixed_atom,
                                            derive_sequence_of_temporal_operators,
                                            NextTransitionFromConcreteState,
                                            get_base_variable,
                                            TimeBetweenLessThanConstant,
                                            DurationOfTransitionLessThanConstant)
from VyPR.Specifications.predicates import changes, calls

class TestSpecificationsBuilder(unittest.TestCase):

    def setUp(self):
        # construct a composite constraint and a single atom
        self.q = ConcreteStateVariable('q')
        self.next_call = self.q.next(calls('f1').during('function'))
        self.simple_atom = self.q.next(calls('f1').during('function')).duration() < 1
        self.mixed_atom = timeBetween(self.q, self.q.next(calls('f1').during('function')).before()) < 1
        self.composite = all_are_true(self.simple_atom, self.mixed_atom)
        self.specification = Specification()\
            .forall(q = changes('string')\
            .during('function'))\
            .check(lambda q : all_are_true(
                    timeBetween(self.q, self.q.next(calls('f1').during('function')).before()) < 1,
                    q.next(calls('f1').during('function')).duration() < 1
                )
            )
    
    def test_is_atomic_constraint(self):
        self.assertTrue(_is_constraint_base(self.simple_atom))
        self.assertTrue(_is_constraint_base(self.mixed_atom))
        self.assertTrue(_is_constraint_base(self.composite))
        self.assertFalse(_is_constraint_base(self.next_call))
    
    def test_is_complete(self):
        self.assertTrue(is_complete(self.simple_atom))
        self.assertTrue(is_complete(self.mixed_atom))
        self.assertTrue(is_complete(self.composite))
        self.assertFalse(is_complete(self.next_call))
    
    def test_is_connective(self):
        self.assertTrue(_is_connective(self.composite))
        self.assertFalse(_is_connective(self.simple_atom))
    
    def test_is_normal_atom(self):
        self.assertTrue(is_normal_atom(self.simple_atom))
        self.assertFalse(is_normal_atom(self.mixed_atom))
        self.assertFalse(is_normal_atom(self.composite))
    
    def test_is_mixed_atom(self):
        self.assertTrue(is_mixed_atom(self.mixed_atom))
        self.assertFalse(is_mixed_atom(self.simple_atom))
        self.assertFalse(is_mixed_atom(self.composite))
    
    def test_derive_sequence_of_temporal_operators_normal_atom(self):
        # compute composition sequence
        composition_sequence_dict = derive_sequence_of_temporal_operators(self.simple_atom)
        composition_sequence = composition_sequence_dict[0]
        # assertions
        self.assertIsInstance(composition_sequence[-1], ConcreteStateVariable)
        self.assertIsInstance(composition_sequence[0], NextTransitionFromConcreteState)
    
    def test_derive_sequence_of_temporal_operators_mixed_atom(self):
        # compute composition sequence
        composition_sequence_dict = derive_sequence_of_temporal_operators(self.mixed_atom)
        # assertions
        lhs_composition_sequence = composition_sequence_dict[0]
        self.assertIsInstance(lhs_composition_sequence[0], ConcreteStateVariable)
        rhs_composition_sequence = composition_sequence_dict[1]
        self.assertIsInstance(rhs_composition_sequence[-1], ConcreteStateVariable)
        self.assertIsInstance(rhs_composition_sequence[0], NextTransitionFromConcreteState)
    
    def test_get_base_variable_normal_atom(self):
        base_variable = get_base_variable(self.simple_atom)
        self.assertEqual(base_variable.get_name(), 'q')
    
    def test_get_base_variable_mixed_atom_lhs(self):
        base_variable = get_base_variable(self.mixed_atom.get_lhs_expression())
        self.assertEqual(base_variable.get_name(), 'q')
    
    def test_get_base_variable_mixed_atom_rhs(self):
        base_variable = get_base_variable(self.mixed_atom.get_rhs_expression())
        self.assertEqual(base_variable.get_name(), 'q')
    
    def test_get_atomic_constraints(self):
        # get the atomic constraints found in self.specification
        atomic_constraints = self.specification.get_constraint().get_atomic_constraints()
        # assertions
        self.assertIsInstance(atomic_constraints[0], DurationOfTransitionLessThanConstant)
        self.assertIsInstance(atomic_constraints[1], TimeBetweenLessThanConstant)