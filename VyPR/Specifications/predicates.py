"""
Module containing classes that model iCFTL predicates.
"""

class predicate():
    pass

class changes(predicate):
    """
    Class for representing the syntax changes(x).during(func)
    """

    def __init__(self, variable):
        self._variable = variable
    
    def during(self, function_name):
        self._during_function = function_name

class calls(predicate):
    """
    Class for representing the syntax calls(f).during(func)
    """

    def __init__(self, function_name):
        self._function_name = function_name
    
    def during(self, function_name):
        self._during_function = function_name