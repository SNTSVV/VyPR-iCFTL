"""
Module containing classes to represent constraints used in an iCFTL specification.

For example, in the specification

forall q in changes(x) : q(x) < 10

q(x) < 10 is a constraint and is represented using the classes in this module.
"""

class ConcreteStateVariable():
    """
    Class to represent a concrete state captured by a quantifier.
    """

    def __init__(self, name):
        self._name = name
    
    def __repr__(self):
        return self._name

    def __call__(self, program_variable_name: str):
        return ValueInConcreteStateVariable(self, program_variable_name)

class TransitionVariable():
    """
    Class to represent a transition captured by a quantifier.
    """

    def __init__(self, name):
        self._name = name
    
    def __repr__(self):
        return self._name

class ValueInConcreteStateVariable():
    """
    Class to represent the value given to a variable by a concrete state.
    """

    def __init__(self, concrete_state_variable, program_variable_name):
        self._concrete_state_variable = concrete_state_variable
        self._program_variable_name = program_variable_name
    
    def __repr__(self):
        return f"{self._concrete_state_variable}({self._program_variable_name})"
    
    def __lt__(self, other):
        if type(other) in [int, str, float]:
            return ValueInConcreteStateLessThanConstant(self, other)

class ValueInConcreteStateLessThanConstant():
    """
    Class to represent the atom q(x) < n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, lhs, rhs):
        self._lhs = lhs
        self._rhs = rhs
    
    def __repr__(self):
        return f"{self._lhs} < {self._rhs}"