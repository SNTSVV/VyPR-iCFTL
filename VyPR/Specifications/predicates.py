"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module containing classes that model iCFTL predicates.
"""

class predicate():
    pass

class changes(predicate):
    """
    Class for representing the syntax changes(x).during(func)
    """

    def __init__(self, program_variable):
        self._program_variable = program_variable
        self._during_function = None
    
    def __repr__(self):
        return f"changes({self._program_variable}).during({self._during_function})"
    
    def __eq__(self, other):
        return (type(self) is type(other)
                and self._program_variable == other._program_variable
                and self._during_function == other._during_function)
    
    def during(self, function_name):
        self._during_function = function_name
        return self
    
    def get_program_variable(self):
        return self._program_variable
    
    def get_during_function(self):
        return self._during_function

class calls(predicate):
    """
    Class for representing the syntax calls(f).during(func)
    """

    def __init__(self, function_name):
        self._function_name = function_name
        self._during_function = None
    
    def __repr__(self):
        return f"calls({self._function_name}).during({self._during_function})"
    
    def __eq__(self, other):
        return (type(self) is type(other)
                and self._function_name == other._function_name
                and self._during_function == other._during_function)
    
    def during(self, function_name):
        self._during_function = function_name
        return self
    
    def get_function_name(self):
        return self._function_name
    
    def get_during_function(self):
        return self._during_function

class future(predicate):
    """
    Class for representing the future predicate for use in quantifiers (which is based on either changes or calls).
    """

    def __init__(self, predicate):
        self._predicate = predicate
    
    def __repr__(self):
        return f"future({self._predicate})"
    
    def get_predicate(self):
        return self._predicate