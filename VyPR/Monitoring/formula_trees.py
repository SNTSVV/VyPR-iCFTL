"""
Module that holds all logic regarding binding/formula tree pairs derived while monitoring for an iCFTL specification.
"""

class FormulaTree():
    """
    Class to model a formula tree.
    
    A formula tree represents part of the current state of the monitor for an iCFTL specification.
    
    It is associated with a sequence of timestamps
    corresponding to when the concrete state/transition for each variable was observed at runtime.
    """

    def __init__(self, timestamps: list, constraint, measurement_dictionary: dict = None):
        """
        Store the list of timestamps that form the binding for this formula tree.
        
        Store the dictionary of measurements, assuming the form
            {atom index : {subatom index : measurement}}
        """
        self._timestamps = timestamps
        self._constraint = constraint
        self._measurement_dictionary = measurement_dictionary
    
    def __repr__(self):
        return f"<FormulaTree timestamps = {self._timestamps} constraint = {self._constraint}>"