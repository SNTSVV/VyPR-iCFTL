"""
Module containing classes that model iCFTL predicates.
"""

from VyPR.Specifications.constraints import ConcreteStateVariable, TransitionVariable

class predicate():
    pass

class changes(predicate):
    """
    Class for representing the syntax changes(x).during(func)
    """

    def __init__(self, variable):
        self._variable = variable
        self._during_function = None
    
    def __repr__(self):
        return f"changes({self._variable}).during({self._during_function})"
    
    def during(self, function_name):
        self._during_function = function_name
        return self
    
    def get_quantifier_variable(self, variable_name):
        """
        Returns an instance of an object representing the variable that
        would be bound to this predicate in a specification.
        """
        return ConcreteStateVariable(variable_name)

class calls(predicate):
    """
    Class for representing the syntax calls(f).during(func)
    """

    def __init__(self, function_name):
        self._function_name = function_name
        self._during_function = None
    
    def __repr__(self):
        return f"calls({self._function_name}).during({self._during_function})"
    
    def during(self, function_name):
        self._during_function = function_name
        return self
    
    def get_quantifier_variable(self, variable_name):
        """
        Returns an instance of an object representing the variable that
        would be bound to this predicate in a specification.
        """
        return TransitionVariable(variable_name)