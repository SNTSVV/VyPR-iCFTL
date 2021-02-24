"""
Module containing classes for construction of iCFTL specifications.

Specifications are constructed hierarchically, as chains of objects.

The root object is always a Specification instance.  This can contain configuration information for the specification.

The first object inside the Specification must be a Forall instance.  This indicates universal quantification.

There can arbitrarily many Forall instances nested.

The final instance in the chain must be a Constraint instance.  This has recursive structure (based on the grammar of iCFTL).
"""

from VyPR.Specifications.predicates import changes, calls, future
from VyPR.Specifications.constraints import Constraint, ConcreteStateVariable, TransitionVariable, Conjunction, Disjunction, Negation, TimeBetween
import VyPR.Logging.logger as logger

class Specification():
    """
    The top-level class for specifications.
    """

    def __init__(self):
        logger.log.info("Instantiating new specification...")
        self.quantifier = None
    
    def __repr__(self):
        """
        Construct the string representation recursively.
        """
        return f"{self.quantifier}"
    
    def get_variable_to_obj_map(self) -> dict:
        """
        Traverse the specification in order to construct a map
        from each variable to the type of object it will hold
        (either a ConcreteState or a Transition instance).

        Note: this function should not try to serialise any objects from the specification
        because serialisation of a Constraint instance requires calling of this function,
        hence the result would be an infinite loop.
        """
        logger.log.info("Deriving map variable names -> variable object from quantifiers")
        # initialise an empty map
        variable_to_obj = {}
        # set the current object to be the top-level specification
        current_obj = self
        # iterate through the structure, using the type Constraint as a place to stop
        logger.log.info("Traversing specification structure")
        while type(current_obj) is not Constraint:
            logger.log.info(f"Processing {type(current_obj)} instance")
            # traverse depending on the type of the current object
            if type(current_obj) is Specification:
                current_obj = current_obj.quantifier
            elif type(current_obj) is Forall:
                # first, add to the map
                # we check the type of the predicate so we know what kind of variable to instantiate
                if type(current_obj.predicate) is changes:
                    variable_to_obj[current_obj.variable] = ConcreteStateVariable(current_obj.variable)
                elif type(current_obj.predicate) is calls:
                    variable_to_obj[current_obj.variable] = TransitionVariable(current_obj.variable)
                elif type(current_obj.predicate) is future:
                    if type(current_obj.predicate._predicate) is changes:
                        variable_to_obj[current_obj.variable] = ConcreteStateVariable(current_obj.variable)
                    elif type(current_obj.predicate._predicate) is calls:
                        variable_to_obj[current_obj.variable] = TransitionVariable(current_obj.variable)
                # in the case of a quantifier, the two possibilities are
                # that the next item to consider is a quantifier or a constraint
                if current_obj.quantifier:
                    current_obj = current_obj.quantifier
                else:
                    # if we arrive at a constraint, the loop
                    # will stop at the next ieration
                    current_obj = current_obj.constraint
        
        logger.log.info(f"Map is {variable_to_obj}")
        
        return variable_to_obj

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

        logger.log.info(f"Adding quantifier with arguments {quantified_variable}")

        # store the quantifier
        self.quantifier = Forall(self, **quantified_variable)

        return self.quantifier

class Forall():
    """
    The class for representing universal quantification in specifications.
    """

    def __init__(self, specification_obj: Specification, **quantified_variable):
        self._specification_obj = specification_obj
        # we will use the fact that either a constraint or a quantifier is stored
        # to determine what the next thing we will see in the structure of the specification is
        self.constraint = None
        self.quantifier = None
        # Note: .keys() does not give a structure with an ordering,
        # so normally converting to a list would be problematic
        # but here we know that there must be one element
        self.variable = list(quantified_variable.keys())[0]
        self.predicate = list(quantified_variable.values())[0]
    
    def __repr__(self):
        if self.constraint:
            # this is the last quantifier, so the next thing to turn into a string is a constraint
            return f"forall {self.variable} in {self.predicate}:\n  {self.constraint}"
        else:
            # this is not the last quantifier - there is another nested inside
            return f"forall {self.variable} in {self.predicate}:\n{self.quantifier}"

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

        logger.log.info(f"Adding quantifier with arguments {quantified_variable}")

        # store the quantifier
        self.quantifier = Forall(self._specification_obj, **quantified_variable)

        return self.quantifier
    
    def check(self, expression):
        """
        Instantiate a top-level Constraint instance with the given constraint lambda.

        The lambda will later be called and supplied with the necessary variables during instrumentation and monitoring.
        """
        # make sure constraint is a lambda
        if type(expression) is not type(lambda:0):
            raise Exception("Constraint given must be a lambda expression.")

        logger.log.info("Setting constraint to check")

        self.constraint = Constraint(self._specification_obj, expression)

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