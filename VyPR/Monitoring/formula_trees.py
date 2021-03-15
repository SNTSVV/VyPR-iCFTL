"""
Module that holds all logic regarding binding/formula tree pairs derived while monitoring for an iCFTL specification.
"""

from VyPR.Specifications.constraints import is_normal_atom, is_mixed_atom

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
        self._atoms = self._constraint.get_atomic_constraints()
        self._measurement_dictionary = measurement_dictionary
    
    def __repr__(self):
        return f"<FormulaTree timestamps = {self._timestamps} constraint = {self._constraint}>"
    
    def update_with_measurement(self, atom_index: int, subatom_index: int):
        """
        Given atom and subatom indices, find the part of the formula tree to update.
        """
    
    def _recurse_on_tree(self, current_obj, measurement, atom_index, subatom_index):
        """
        Recurse on the formula tree.

        If we encounter an object that is a normal or mixed atom,
        we don't recurse further and instead see if we can update it.

        If we encounter an object that is not a normal or mixed atom,
        we recurse and then check to see whether a truth value can be declared
        for that part of the formula tree.
        """
        if is_normal_atom(current_obj) or is_mixed_atom(current_obj):
            # base case
            # check to see whether current_obj matches atom_index
            if self._atoms.index(current_obj) == atom_index:
                # return the answer given by the atom under the measurement given
                # the answer can be true, false or inconclusive (for mixed atoms)
                return current_obj.check(measurement, subatom_index)
            else:
                # this isn't the atom we need, so just return it
                return current_obj
        else:
            # recursive case
            # we either have a disjunction, conjunction or negation

            # in the disjunction case, we recurse on each disjunct and see
            # if any gives true

            # in the conjunction case, we recurse on each conjunct and see
            # if any gives false

            # in the negation case, we see if the operand gives a truth value