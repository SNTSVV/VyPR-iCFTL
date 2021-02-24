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
        return ValueInConcreteState(self, program_variable_name)

class ValueInConcreteState():
    """
    Class to represent the value given to a variable by a concrete state.
    """

    def __init__(self, concrete_state_expression, program_variable_name):
        self._concrete_state_expression = concrete_state_expression
        self._program_variable_name = program_variable_name
    
    def __repr__(self):
        return f"{self._concrete_state_expression}({self._program_variable_name})"
    
    def __lt__(self, other):
        if type(other) in [int, str, float]:
            return ValueInConcreteStateLessThanConstant(self, other)
    
    def __gt__(self, other):
        if type(other) in [int, str, float]:
            return ValueInConcreteStateGreaterThanConstant(self, other)

class ValueInConcreteStateLessThanConstant():
    """
    Class to represent the atom q(x) < n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, value_expression, constant):
        self._value_expression = value_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._value_expression} < {self._constant}"

class ValueInConcreteStateGreaterThanConstant():
    """
    Class to represent the atom q(x) > n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, value_expression, constant):
        self._value_expression = value_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._value_expression} > {self._constant}"

class TransitionVariable():
    """
    Class to represent a transition captured by a quantifier.
    """

    def __init__(self, name):
        self._name = name
    
    def __repr__(self):
        return self._name
    
    def duration(self):
        return DurationOfTransition(self)

class DurationOfTransition():
    """
    Class to represent the result of calling .duration() on a transition.
    """

    def __init__(self, transition_expression):
        self._transition_expression = transition_expression
    
    def __repr__(self):
        return f"{self._transition_expression}.duration()"
    
    def __lt__(self, other):
        if type(other) in [int, float]:
            return DurationOfTransitionLessThanConstant(self, other)
        if type(other) in [int, float]:
            return DurationOfTransitionGreaterThanConstant(self, other)

class DurationOfTransitionLessThanConstant():
    """
    Class to represent the comparison of a transition duration with a constant.
    """

    def __init__(self, transition_duration, constant):
        self._transition_duration = transition_duration
        self._constant = constant
    
    def __repr__(self):
        return f"{self._transition_duration} < {self._constant}"

class DurationOfTransitionGreaterThanConstant():
    """
    Class to represent the comparison of a transition duration with a constant.
    """

    def __init__(self, transition_duration, constant):
        self._transition_duration = transition_duration
        self._constant = constant
    
    def __repr__(self):
        return f"{self._transition_duration} > {self._constant}"

class Conjunction():
    """
    Class to represent a conjunction of 2 or more constraints.
    """

    def __init__(self, *conjuncts):
        self._conjuncts = conjuncts
    
    def __repr__(self):
        serialised_conjuncts = map(str, self._conjuncts)
        return " and ".join(serialised_conjuncts)
    
    def get_conjuncts(self) -> list:
        return self._conjuncts

class Disjunction():
    """
    Class to represent a disjunction of 2 or more constraints.
    """

    def __init__(self, *disjuncts):
        self._disjuncts = disjuncts
    
    def __repr__(self):
        serialised_disjuncts = map(str, self._disjuncts)
        return " or ".join(serialised_disjuncts)
    
    def get_disjuncts(self) -> list:
        return self._disjuncts

class Negation():
    """
    Class to represent the negation.

    Negation should be propagated through to atomic constraints.
    """

    def __init__(self, operand):
        self._operand = operand
    
    def __repr__(self):
        return f"not( {self._operand} )"
    
    def get_operand(self):
        return self._operand