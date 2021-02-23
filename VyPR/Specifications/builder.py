"""
Module containing classes for construction of iCFTL specifications.

Specifications are constructed hierarchically, as chains of objects.

The root object is always a Specification instance.  This can contain configuration information for the specification.

The first object inside the Specification must be a Forall instance.  This indicates universal quantification.

There can arbitrarily many Forall instances nested.

The final instance in the chain must be a Constraint instance.  This has recursive structure (based on the grammar of iCFTL).
"""

from VyPR.Specifications.predicates import changes, calls

class Specification():
    """
    The top-level class for specifications.
    """

    def __init__(self):
        self.quantifier = None
    
    def __repr__(self):
        """
        Construct the string representation recursively.
        """
        return f"{self.quantifier}"

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
        if type(predicate) not in [changes, calls]:
            raise Exception(f"Type '{type(predicate).__name__}' not supported.")

        # store the quantifier
        self.quantifier = Forall(self, **quantified_variable)

        return self.quantifier

class Forall():
    """
    The class for representing universal quantification in specifications.
    """

    def __init__(self, specification_obj, **quantified_variable):
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
            return f"forall {self.variable} in {self.predicate}\n  {self.constraint}"
        else:
            # this is not the last quantifier - there is another nested inside
            return f"forall {self.variable} in {self.predicate}\n{self.quantifier}"

    def forall(self, **quantified_variable):
        """
        **quantified variable must be a dictionary with only one key - the variable being given.
        The value associated with the variable must be a Predicate instance.
        """
        # if there is more than 1 variable, raise an exception
        if len(quantified_variable.keys()) > 1:
            raise Exception("A single variable must be given for each level of universal quantification.")

        # check the type of the value
        predicate = quantified_variable.values()[0]
        if type(predicate) not in [changes, calls]:
            raise Exception(f"Type '{type(predicate).__name__}' not supported.")

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

        self.constraint = Constraint(self._specification_obj, expression)

        return self._specification_obj


class Constraint():
    """
    The class for representing the recursive structure of the quantifier-free part of iCFTL specifications.
    """

    def __init__(self, specification_obj, expression):
        self._specification_obj = specification_obj
        self._expression = expression
    
    def __repr__(self):
        return f"<constraint>"