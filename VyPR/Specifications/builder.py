"""
Module containing classes for construction of iCFTL specifications.

Specifications are constructed hierarchically, as chains of objects.

The root object is always a Specification instance.  This can contain configuration information for the specification.

The first object inside the Specification must be a Forall instance.  This indicates universal quantification.

There can arbitrarily many Forall instances nested.

The final instance in the chain must be a Constraint instance.  This has recursive structure (based on the grammar of iCFTL).
"""
import logging
logger = logging.getLogger("VyPR")

from VyPR.Specifications.predicates import changes, calls, future
from VyPR.Specifications.constraints import (Constraint,
                                            ConstraintBase,
                                            ConcreteStateExpression,
                                            TransitionExpression,
                                            ConcreteStateVariable,
                                            TransitionVariable,
                                            Conjunction,
                                            Disjunction,
                                            Negation,
                                            TimeBetween,
                                            ValueInConcreteStateEqualsConstant,
                                            ValueInConcreteStateLessThanConstant,
                                            ValueInConcreteStateGreaterThanConstant,
                                            DurationOfTransitionLessThanConstant,
                                            DurationOfTransitionGreaterThanConstant,
                                            ConcreteStateBeforeTransition,
                                            ConcreteStateAfterTransition,
                                            NextTransitionFromConcreteState,
                                            NextConcreteStateFromConcreteState,
                                            NextTransitionFromTransition,
                                            NextConcreteStateFromTransition,
                                            TimeBetweenLessThanConstant)

class Specification():
    """
    The top-level class for specifications.
    """

    def __init__(self):
        logger.info("Instantiating new specification...")
        self._quantifier = None
    
    def __repr__(self):
        """
        Construct the string representation recursively.
        """
        return f"{self._quantifier}"
    
    def get_quantifier(self):
        return self._quantifier
    
    def get_variable_to_obj_map(self) -> dict:
        """
        Traverse the specification in order to construct a map
        from each variable to the type of object it will hold
        (either a ConcreteState or a Transition instance).

        Note: this function should not try to serialise any objects from the specification
        because serialisation of a Constraint instance requires calling of this function,
        hence the result would be an infinite loop.
        """
        logger.info("Deriving map variable names -> variable object from quantifiers")
        # initialise an empty map
        variable_to_obj = {}
        # set the current object to be the top-level specification
        current_obj = self
        # iterate through the structure, using the type Constraint as a place to stop
        logger.info("Traversing specification structure")
        while type(current_obj) is not Constraint:
            logger.info(f"current_obj = {type(current_obj)}")
            # traverse depending on the type of the current object
            if type(current_obj) is Specification:
                current_obj = current_obj._quantifier
            elif type(current_obj) is Forall:
                # first, add to the map
                # we check the type of the predicate so we know what kind of variable to instantiate
                if type(current_obj._predicate) is changes:
                    variable_to_obj[current_obj._variable] = ConcreteStateVariable(current_obj._variable)
                elif type(current_obj._predicate) is calls:
                    variable_to_obj[current_obj._variable] = TransitionVariable(current_obj._variable)
                elif type(current_obj._predicate) is future:
                    if type(current_obj._predicate._predicate) is changes:
                        variable_to_obj[current_obj._variable] = ConcreteStateVariable(current_obj._variable)
                    elif type(current_obj._predicate._predicate) is calls:
                        variable_to_obj[current_obj._variable] = TransitionVariable(current_obj._variable)
                # in the case of a quantifier, the two possibilities are
                # that the next item to consider is a quantifier or a constraint
                if current_obj._quantifier:
                    current_obj = current_obj._quantifier
                else:
                    # if we arrive at a constraint, the loop
                    # will stop at the next ieration
                    current_obj = current_obj._constraint
        
        logger.info(f"variable_to_obj = {variable_to_obj}")
        
        return variable_to_obj
    
    def get_variables(self) -> list:
        """
        Traverse the specification in order to construct a list of variables.

        The order of the list matches the order in which the variables occur in quantifiers.
        """
        logger.info("Deriving list of variables from quantifiers")
        # initialise an empty list
        variables = []
        # set the current object to be the top-level specification
        current_obj = self
        # iterate through the structure, using the type Constraint as a place to stop
        logger.info("Traversing specification structure")
        while type(current_obj) is not Constraint:
            logger.info(f"current_obj = {type(current_obj)}")
            # traverse depending on the type of the current object
            if type(current_obj) is Specification:
                current_obj = current_obj._quantifier
            elif type(current_obj) is Forall:
                # first, add to the map
                # we check the type of the predicate so we know what kind of variable to instantiate
                if type(current_obj._predicate) is changes:
                    variables.append(current_obj._variable)
                elif type(current_obj._predicate) is calls:
                    variables.append(current_obj._variable)
                elif type(current_obj._predicate) is future:
                    if type(current_obj._predicate._predicate) is changes:
                        variables.append(current_obj._variable)
                    elif type(current_obj._predicate._predicate) is calls:
                        variables.append(current_obj._variable)
                # in the case of a quantifier, the two possibilities are
                # that the next item to consider is a quantifier or a constraint
                if current_obj._quantifier:
                    current_obj = current_obj._quantifier
                else:
                    # if we arrive at a constraint, the loop
                    # will stop at the next ieration
                    current_obj = current_obj._constraint
        
        return variables
    
    def get_function_names_used(self):
        """
        Traverse the specification and, each time a predicate is encountered, extract the function
        name used and add to the list.
        """
        # initialise an empty list of function names
        all_function_names = []
        # initialise stack wth top-level Specification object for traversal
        stack = [self]
        # process the stack while it is not empty
        while len(stack) > 0:
            # get the top element from the stack
            top = stack.pop()
            # based on the type, add child elements to the stack or add a new function name
            # to the list
            if type(top) in [changes, calls]:
                all_function_names.append(top._during_function)
            elif type(top) is future:
                stack.append(top.get_predicate())
            elif type(top) is Specification:
                stack.append(top.get_quantifier())
            elif type(top) is Forall:
                # add the predicate to the stack
                stack.append(top.get_predicate())
                # also, carry on traversing the specification
                if top.get_quantifier():
                    stack.append(top.get_quantifier())
                else:
                    stack.append(top.get_constraint())
            elif type(top) is Constraint:
                stack.append(top.instantiate())
            elif type(top) is Conjunction:
                stack += top.get_conjuncts()
            elif type(top) is Disjunction:
                stack += top.get_disjuncts()
            elif type(top) is Negation:
                stack.append(top.get_operand())
            elif type(top) in [ValueInConcreteStateEqualsConstant, ValueInConcreteStateLessThanConstant, ValueInConcreteStateGreaterThanConstant]:
                stack.append(top.get_value_expression().get_concrete_state_expression())
            elif type(top) in [ConcreteStateBeforeTransition, ConcreteStateAfterTransition]:
                stack.append(top.get_transition_expression())
            elif type(top) in [DurationOfTransitionLessThanConstant, DurationOfTransitionGreaterThanConstant]:
                stack.append(top.get_transition_duration_obj().get_transition_expression())
            elif type(top) in [NextTransitionFromConcreteState, NextConcreteStateFromConcreteState]:
                stack.append(top.get_predicate())
            elif type(top) in [NextTransitionFromTransition, NextConcreteStateFromTransition]:
                stack.append(top.get_predicate())
            elif type(top) is TimeBetweenLessThanConstant:
                # traverse both arguments to the timeBetween operator
                stack.append(top.get_time_between_expression().get_lhs_expression())
                stack.append(top.get_time_between_expression().get_rhs_expression())
        
        all_function_names = list(set(all_function_names))
            
        return all_function_names
    
    def get_constraint(self):
        """
        Traverse the specification until a constraint is reached.
        """
        # set the current object to be the first quantifier
        current_obj = self._quantifier
        # iterate through the structure, using the type Constraint as a place to stop
        while type(current_obj) is not Constraint:
            # traverse depending on the type of the current object
            if type(current_obj) is Specification:
                current_obj = current_obj.get_quantifier()
            elif type(current_obj) is Forall:
                # in the case of a quantifier, the two possibilities are
                # that the next item to consider is a quantifier or a constraint
                if current_obj.get_quantifier():
                    current_obj = current_obj.get_quantifier()
                else:
                    # if we arrive at a constraint, the loop
                    # will stop at the next ieration
                    current_obj = current_obj.get_constraint()
        return current_obj

    def forall(self, **quantified_variable):
        """
        **quantified variable must be a dictionary with only one key - the variable being given.
        The value associated with the variable must be a Predicate instance.
        """
        # if there is more than 1 variable, raise an exception
        if len(quantified_variable.keys()) > 1:
            raise Exception("A single variable must be given for each level of universal quantification.")

        # check the type of the value
        predicate = list(quantified_variable.values())[0]
        if type(predicate) not in [changes, calls, future]:
            raise Exception(f"Type '{type(predicate).__name__}' not supported.")

        # make sure the predicate is complete
        variable = list(quantified_variable.keys())[0]
        if not predicate._during_function:
            raise Exception(f"Predicate used for variable {variable} not complete")

        logger.info(f"Adding quantifier with arguments {quantified_variable}")

        # store the quantifier
        self._quantifier = Forall(self, **quantified_variable)

        return self._quantifier

class Forall():
    """
    The class for representing universal quantification in specifications.
    """

    def __init__(self, specification_obj: Specification, **quantified_variable):
        self._specification_obj = specification_obj
        # we will use the fact that either a constraint or a quantifier is stored
        # to determine what the next thing we will see in the structure of the specification is
        self._constraint = None
        self._quantifier = None
        # Note: .keys() does not give a structure with an ordering,
        # so normally converting to a list would be problematic
        # but here we know that there must be one element
        self._variable = list(quantified_variable.keys())[0]
        self._predicate = list(quantified_variable.values())[0]
    
    def __repr__(self):
        if self._constraint:
            # this is the last quantifier, so the next thing to turn into a string is a constraint
            return f"forall {self._variable} in {self._predicate}:\n  {self._constraint}"
        else:
            # this is not the last quantifier - there is another nested inside
            return f"forall {self._variable} in {self._predicate}:\n{self._quantifier}"
    
    def get_specification_obj(self):
        return self._specification_obj
    
    def get_quantifier(self):
        return self._quantifier
    
    def get_constraint(self):
        return self._constraint
    
    def get_predicate(self):
        return self._predicate
    
    def get_variable(self):
        return self._variable

    def forall(self, **quantified_variable):
        """
        **quantified variable must be a dictionary with only one key - the variable being given.
        The value associated with the variable must be a Predicate instance.
        """
        # if there is more than 1 variable, raise an exception
        if len(quantified_variable.keys()) > 1:
            raise Exception("A single variable must be given for each level of universal quantification.")

        # check the type of the value - this is not the first quantifier,
        # so the type must be future
        predicate = list(quantified_variable.values())[0]
        if type(predicate) is not future:
            raise Exception(f"Type '{type(predicate).__name__}' not supported.")

        # make sure the predicate is complete
        variable = list(quantified_variable.keys())[0]
        if not predicate._predicate._during_function:
            raise Exception(f"Predicate used for variable {variable} not complete")

        logger.info(f"Initialising new instance of Forall with quantified_variable = {quantified_variable}")

        # store the quantifier
        self._quantifier = Forall(self._specification_obj, **quantified_variable)

        return self._quantifier
    
    def check(self, expression):
        """
        Instantiate a top-level Constraint instance with the given constraint lambda.

        The lambda will later be called and supplied with the necessary variables during instrumentation and monitoring.
        """
        # make sure constraint is a lambda
        if type(expression) is not type(lambda:0):
            raise Exception("Constraint given must be a lambda expression.")

        logger.info("Setting self._constraint to new Constraint instance")

        self._constraint = Constraint(self._specification_obj, expression)

        return self._specification_obj

"""
Syntax sugar functions.
"""

def all_are_true(*conjuncts):
    """
    Encode a conjunction.
    """
    return Conjunction(*conjuncts)

def one_is_true(*disjuncts):
    """
    Encode a disjunction.
    """
    return Disjunction(*disjuncts)

def not_true(operand):
    """
    Given an operand, instantiate either a single negation,
    or another structure by propagating negation through to atomic constraints.
    """
    if type(operand) is Conjunction:
        # rewrite negation of conjunction as disjunction of negations
        return Disjunction(*map(lambda conjunct : not_true(conjunct), operand.get_conjuncts()))
    elif type(operand) is Disjunction:
        # rewrite negation of disjunction as conjunction of negations
        return Conjunction(*map(lambda disjunct : not_true(disjunct), operand.get_disjuncts()))
    elif type(operand) is Negation:
        # eliminate double negation
        return operand.get_operand()
    else:
        # assume operand is atomic constraint
        return Negation(operand)

def timeBetween(concrete_state_expression_1, concrete_state_expression_2):
    return TimeBetween(concrete_state_expression_1, concrete_state_expression_2)