"""
Module containing classes to represent constraints used in an iCFTL specification.

For example, in the specification

forall q in changes(x) : q(x) < 10

q(x) < 10 is a constraint and is represented using the classes in this module.
"""

from VyPR.Specifications.predicates import changes, calls

"""
Propositional connectives.
"""

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

"""
Types of expressions.
"""

class ConcreteStateExpression():
    """
    Class to represent a concrete state (whether bound to a variable or seen elsewhere).
    """

    def next(self, predicate):
        """
        Given a predicate, instantiate an object representing either the next satisfying concrete
        state or the next satisfying transition.
        """
        if type(predicate) is calls:
            return NextTransitionFromConcreteState(self, predicate)
        elif type(predicate) is changes:
            return NextConcreteStateFromConcreteState(self, predicate)
    
    def __call__(self, program_variable_name: str):
        return ValueInConcreteState(self, program_variable_name)

class TransitionExpression():
    """
    Class to represent a transition (whether bound to a variable or seen elsewhere).
    """

    def duration(self):
        return DurationOfTransition(self)
    
    def next(self, predicate):
        """
        Given a predicate, instantiate an object representing either the next satisfying concrete
        state or the next satisfying transition.
        """
        if type(predicate) is calls:
            return NextTransitionFromTransition(self, predicate)
        elif type(predicate) is changes:
            return NextConcreteStateFromTransition(self, predicate)

"""
Types of variables.
"""

class ConcreteStateVariable(ConcreteStateExpression):
    """
    Class to represent a concrete state captured by a quantifier.
    """

    def __init__(self, name):
        self._name = name
    
    def __repr__(self):
        return self._name

class TransitionVariable(TransitionExpression):
    """
    Class to represent a transition captured by a quantifier.
    """

    def __init__(self, name):
        self._name = name
    
    def __repr__(self):
        return self._name

"""
Attributes of concrete states.
"""

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
    
    def equals(self, other):
        if type(other) in [int, str, float, bool]:
            return ValueInConcreteStateEqualsConstant(self, other)

"""
Atomic constraints for concrete states.
"""

class ValueInConcreteStateEqualsConstant():
    """
    Class to represent the atom q(x) == n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, value_expression, constant):
        self._value_expression = value_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._value_expression}.equals({self._constant})"

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

"""
Attributes of transitions.
"""

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

"""
Atomic constraints over transitions.
"""

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

"""
Temporal operators.
"""

class NextTransitionFromConcreteState(TransitionExpression):
    """
    Class to represent the atom X.next(P) for a concrete state expression X and a predicate P
    identifying transitions.
    """

    def __init__(self, concrete_state_expression, predicate):
        self._concrete_state_expression = concrete_state_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._concrete_state_expression}.next({self._predicate})"


class NextConcreteStateFromConcreteState(ConcreteStateExpression):
    """
    Class to represent the atom X.next(P) for a concrete state expression X and a predicate P
    identifying concrete states.
    """

    def __init__(self, concrete_state_expression, predicate):
        self._concrete_state_expression = concrete_state_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._concrete_state_expression}.next({self._predicate})"

class NextTransitionFromTransition(TransitionExpression):
    """
    Class to represent the atom X.next(P) for a concrete state expression X and a predicate P
    identifying transitions.
    """

    def __init__(self, transition_expression, predicate):
        self._transition_expression = transition_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._transition_expression}.next({self._predicate})"


class NextConcreteStateFromTransition(ConcreteStateExpression):
    """
    Class to represent the atom X.next(P) for a concrete state expression X and a predicate P
    identifying concrete states.
    """

    def __init__(self, transition_expression, predicate):
        self._transition_expression = transition_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._transition_expression}.next({self._predicate})"