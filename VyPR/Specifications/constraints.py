"""
Module containing classes to represent constraints used in an iCFTL specification.

For example, in the specification

forall q in changes(x) : q(x) < 10

q(x) < 10 is a constraint and is represented using the classes in this module.
"""

from VyPR.Specifications.predicates import changes, calls
import VyPR.Logging.logger as logger

class Constraint():
    """
    Class for representing the recursive structure of the quantifier-free part of iCFTL specifications.
    """

    def __init__(self, specification_obj, constraint):
        self._specification_obj = specification_obj
        self._constraint = constraint
    
    def __repr__(self):
        executed_lambda = self.instantiate_constraint()
        if ConstraintBase not in type(executed_lambda).__bases__:
            # TODO: indicate which part of the constraint is not complete
            logger.log.info("Constraint given in specification is not complete:")
            logger.log.info(str(executed_lambda))
            raise Exception("Constraint given in specification is not complete.")
        return str(executed_lambda)
    
    def instantiate_constraint(self):
        """
        Determine the set of variables from quantifiers and instantiate the quantifier-free
        part of the specification.
        """
        arguments = self._specification_obj.get_variable_to_obj_map()
        executed_lambda = self._constraint(**arguments)
        return executed_lambda
    
    def get_constraint(self):
        return self.instantiate_constraint()

class ConstraintBase():
    """
    Class for representing the root of a combination of constraints.
    """

    pass

"""
Propositional connectives.
"""

class Conjunction(ConstraintBase):
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

class Disjunction(ConstraintBase):
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

class Negation(ConstraintBase):
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
    
    def before(self):
        """
        Instantiate a ConcreteStateBeforeTransition object.
        """
        return ConcreteStateBeforeTransition(self)
    
    def after(self):
        """
        Instantiate a ConcreteStateBeforeTransition object.
        """
        return ConcreteStateAfterTransition(self)

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
    
    def get_concrete_state_expression(self):
        return self._concrete_state_expression
    
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

class ValueInConcreteStateEqualsConstant(ConstraintBase):
    """
    Class to represent the atomic constraint q(x) == n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, value_expression, constant):
        self._value_expression = value_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._value_expression}.equals({self._constant})"
    
    def get_value_expression(self):
        return self._value_expression

class ValueInConcreteStateLessThanConstant(ConstraintBase):
    """
    Class to represent the atomic constraint q(x) < n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, value_expression, constant):
        self._value_expression = value_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._value_expression} < {self._constant}"
    
    def get_value_expression(self):
        return self._value_expression

class ValueInConcreteStateGreaterThanConstant(ConstraintBase):
    """
    Class to represent the atomic constraint q(x) > n for a concrete state variable q, a program variable x
    and a constant n.
    """

    def __init__(self, value_expression, constant):
        self._value_expression = value_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._value_expression} > {self._constant}"
    
    def get_value_expression(self):
        return self._value_expression

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
    
    def get_transition_expression(self):
        return self._transition_expression
    
    def __lt__(self, other):
        if type(other) in [int, float]:
            return DurationOfTransitionLessThanConstant(self, other)
        if type(other) in [int, float]:
            return DurationOfTransitionGreaterThanConstant(self, other)

class ConcreteStateBeforeTransition(ConcreteStateExpression):
    """
    Class to represent the first concrete state in a transition.
    """

    def __init__(self, transition_expression):
        self._transition_expression = transition_expression
    
    def __repr__(self):
        return f"{self._transition_expression}.before()"
    
    def get_transition_expression(self):
        return self._transition_expression

class ConcreteStateAfterTransition(ConcreteStateExpression):
    """
    Class to represent the second concrete state in a transition.
    """

    def __init__(self, transition_expression):
        self._transition_expression = transition_expression
    
    def __repr__(self):
        return f"{self._transition_expression}.after()"
    
    def get_transition_expression(self):
        return self._transition_expression

"""
Atomic constraints over transitions.
"""

class DurationOfTransitionLessThanConstant(ConstraintBase):
    """
    Class to represent the comparison of a transition duration with a constant.
    """

    def __init__(self, transition_duration, constant):
        self._transition_duration = transition_duration
        self._constant = constant
    
    def __repr__(self):
        return f"{self._transition_duration} < {self._constant}"
    
    def get_transition_duration_obj(self):
        return self._transition_duration

class DurationOfTransitionGreaterThanConstant(ConstraintBase):
    """
    Class to represent the comparison of a transition duration with a constant.
    """

    def __init__(self, transition_duration, constant):
        self._transition_duration = transition_duration
        self._constant = constant
    
    def __repr__(self):
        return f"{self._transition_duration} > {self._constant}"
    
    def get_transition_duration_obj(self):
        return self._transition_duration

"""
Temporal operators.
"""

class NextTransitionFromConcreteState(TransitionExpression):
    """
    Class to represent the atomic constraint X.next(P) for a concrete state expression X and a predicate P
    identifying transitions.
    """

    def __init__(self, concrete_state_expression, predicate):
        self._concrete_state_expression = concrete_state_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._concrete_state_expression}.next({self._predicate})"
    
    def get_concrete_state_expression(self):
        return self._concrete_state_expression
    
    def get_predicate(self):
        return self._predicate


class NextConcreteStateFromConcreteState(ConcreteStateExpression):
    """
    Class to represent the atomic constraint X.next(P) for a concrete state expression X and a predicate P
    identifying concrete states.
    """

    def __init__(self, concrete_state_expression, predicate):
        self._concrete_state_expression = concrete_state_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._concrete_state_expression}.next({self._predicate})"
    
    def get_concrete_state_expression(self):
        return self._concrete_state_expression
    
    def get_predicate(self):
        return self._predicate

class NextTransitionFromTransition(TransitionExpression):
    """
    Class to represent the atomic constraint X.next(P) for a concrete state expression X and a predicate P
    identifying transitions.
    """

    def __init__(self, transition_expression, predicate):
        self._transition_expression = transition_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._transition_expression}.next({self._predicate})"
    
    def get_transition_expression(self):
        return self._transition_expression
    
    def get_predicate(self):
        return self._predicate


class NextConcreteStateFromTransition(ConcreteStateExpression):
    """
    Class to represent the atomic constraint X.next(P) for a concrete state expression X and a predicate P
    identifying concrete states.
    """

    def __init__(self, transition_expression, predicate):
        self._transition_expression = transition_expression
        self._predicate = predicate
    
    def __repr__(self):
        return f"{self._transition_expression}.next({self._predicate})"
    
    def get_transition_expression(self):
        return self._transition_expression
    
    def get_predicate(self):
        return self._predicate

"""
Measurement operators.
"""

class TimeBetween():
    """
    Class to represent the timeBetween operator.
    """

    def __init__(self, concrete_state_expression_1, concrete_state_expression_2):
        if (ConcreteStateExpression not in type(concrete_state_expression_1).__bases__
            or ConcreteStateExpression not in type(concrete_state_expression_2).__bases__):
            raise Exception("timeBetween arguments must be states.")
        self._concrete_state_expression_1 = concrete_state_expression_1
        self._concrete_state_expression_2 = concrete_state_expression_2
    
    def __repr__(self):
        return f"timeBetween({self._concrete_state_expression_1}, {self._concrete_state_expression_2})"
    
    def __lt__(self, other):
        if type(other) in [int, float]:
            return TimeBetweenLessThanConstant(self, other)
    
    def get_lhs_concrete_state_expression(self):
        return self._concrete_state_expression_1
    
    def get_rhs_concrete_state_expression(self):
        return self._concrete_state_expression_2

class TimeBetweenLessThanConstant(ConstraintBase):
    """
    Class to represent the atomic constraint timeBetween(q, q') < n for some numerical constant n.
    """

    def __init__(self, time_between_expression, constant):
        self._time_between_expression = time_between_expression
        self._constant = constant
    
    def __repr__(self):
        return f"{self._time_between_expression} < {self._constant}"
    
    def get_time_between_expression(self):
        return self._time_between_expression