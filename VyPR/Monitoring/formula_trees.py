"""
Module that holds all logic regarding binding/formula tree pairs derived while monitoring for an iCFTL specification.
"""

from VyPR.Specifications.constraints import is_normal_atom, is_mixed_atom, Conjunction, Disjunction, Negation

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
        self._formula_tree = constraint.instantiate()
        self._atoms = constraint.get_atomic_constraints()
        self._measurement_dictionary = measurement_dictionary
    
    def __repr__(self):
        return f"<FormulaTree timestamps = {self._timestamps} formula tree = {self._formula_tree}>"
    
    def get_timestamps(self):
        return self._timestamps
    
    def get_configuration(self):
        return self._formula_tree
    
    def update_with_measurement(self, measurement, atom_index: int, subatom_index: int):
        """
        Given a measurement, atom and subatom indices, update the formula tree
        """
        # recurse on the formula tree
        # assign the result in case there is a truth value
        self._formula_tree = self._recurse_on_tree(self._formula_tree, measurement, atom_index, subatom_index)
        return self._formula_tree
    
    def _recurse_on_tree(self, current_obj, measurement, atom_index: int, subatom_index: int):
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
            # recursive cases
            # we either have a disjunction, conjunction or negation

            # in the disjunction case, we recurse on each disjunct and see
            # if any gives true
            if type(current_obj) is Disjunction:
                # iterate through the operands, checking whether any are evaluated to True
                disjuncts = current_obj.get_disjuncts()
                for (index, disjunct) in enumerate(disjuncts):
                    # replace the disjunct with a new value (this may just be the old value if
                    # nothing could be changed given the measurement)
                    disjuncts[index] = self._recurse_on_tree(disjunct, measurement, atom_index, subatom_index)
                    # explicitly check for True
                    if disjuncts[index] == True:
                        # return True to replace current_obj with True in its parent formula
                        return True

            # in the conjunction case, we recurse on each conjunct and see
            # if any gives false
            if type(current_obj) is Conjunction:
                # iterate through the operands, checking whether any are evaluated to False
                # (or whether all are True)
                conjuncts = current_obj.get_conjuncts()
                # count number of True occurrences so we can check for all conjuncts being true
                number_of_trues = 0
                for (index, _) in enumerate(conjuncts):
                    # replace the conjunct with a new value (this may just be the old value if
                    # nothing could be changed given the measurement)
                    conjuncts[index] = self._recurse_on_tree(conjuncts[index], measurement, atom_index, subatom_index)
                    # explicitly check for False
                    if conjuncts[index] == False:
                        # return False to replace current_obj with False in its parent formula
                        return False
                    elif conjuncts[index] == True:
                        # increase the number of Trues
                        number_of_trues += 1
                # check for all conjuncts being True
                if number_of_trues == len(conjuncts):
                    return True

            # in the negation case, we see if the operand gives a truth value
            if type(current_obj) is Negation:
                # recurse on the negation operand, returning True or False if the operand gives a truth value
                current_obj.operand = self._recurse_on_tree(current_obj.operand, measurement, atom_index, subatom_index)
                # check truth value
                if current_obj.operand == True:
                    # negation can be evaluated to False
                    return False
                elif current_obj.operand == False:
                    # negation can be evaluted to True
                    return True
            
            return current_obj