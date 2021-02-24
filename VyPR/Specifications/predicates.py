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
        self._during_function = None
    
    def __repr__(self):
        return f"changes({self._variable}).during({self._during_function})"
    
    def during(self, function_name):
        self._during_function = function_name
        return self

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

class future(predicate):
    """
    Class for representing the future predicate for use in quantifiers (which is based on either changes or calls).
    """

    def __init__(self, predicate):
        self._predicate = predicate
    
    def __repr__(self):
        return f"future({self._predicate})"