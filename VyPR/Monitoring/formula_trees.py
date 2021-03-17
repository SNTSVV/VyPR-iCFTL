"""
Module that holds all logic regarding binding/formula tree pairs derived while monitoring for an iCFTL specification.
"""

from VyPR.Specifications.constraints import is_normal_atom, is_mixed_atom, get_base_variable, Conjunction, Disjunction, Negation

class FormulaTree():
    """
    Class to model a formula tree.
    
    A formula tree represents part of the current state of the monitor for an iCFTL specification.
    
    It is associated with a sequence of timestamps
    corresponding to when the concrete state/transition for each variable was observed at runtime.
    """

    def __init__(self, timestamps: list, constraint, variables: list, measurement_dictionary: dict = {}):
        """
        Store the list of timestamps that form the binding for this formula tree.
        
        Store the constraint to which the formula tree will correspond.

        Store the list of variables from the specification (in order of quantifiers).

        Store the dictionary of measurements, assuming the form
            {atom index : {subatom index : measurement}}
        """
        self._timestamps = timestamps
        self._formula_tree = constraint.instantiate()
        self._atoms = constraint.get_atomic_constraints()
        self._variables = variables
        self._measurement_dictionary = measurement_dictionary

        # run the formula tree update with respect to the measurement dictionary already given
        for atom_index in self._measurement_dictionary:
            for subatom_index in self._measurement_dictionary[atom_index]:
                measurement = self._measurement_dictionary[atom_index][subatom_index]
                self.update_with_measurement(measurement, atom_index, subatom_index)
    
    def __repr__(self):
        return f"<FormulaTree timestamps = {self._timestamps} formula tree = {self._formula_tree}>"
    
    def get_timestamps(self):
        return self._timestamps
    
    def get_configuration(self):
        return self._formula_tree
    
    def get_measurements_dictionary(self):
        return self._measurement_dictionary
    
    def get_measurements_for_variable_index(self, variable_index):
        """
        For each atom index/subatom index pair in self._measurement_dictionary, get the base variable
        and return the sub-dictionary containing only the atom index/subatom index pairs
        to which all variables up to and excluding the one at variable_index are relevant.
        """
        # construct a new, empty dictionary
        final_dictionary = {}
        # iterate through the dictionary
        for atom_index in self._measurement_dictionary:
            for subatom_index in self._measurement_dictionary[atom_index]:
                # get the atom with atom_index
                relevant_atom = self._atoms[atom_index]
                # get the relevant expression based subatom_index
                expression = relevant_atom.get_expression(subatom_index)
                # get base variable of expression
                base_variable = get_base_variable(expression)
                base_variable_name = base_variable.get_name()
                # check whether the base variable has index variable_index
                if self._variables.index(base_variable_name) < variable_index:
                    if atom_index in final_dictionary:
                        if subatom_index not in final_dictionary[atom_index]:
                            final_dictionary[atom_index][subatom_index] = self._measurement_dictionary[atom_index][subatom_index]
                    else:
                        final_dictionary[atom_index] = {
                            subatom_index: self._measurement_dictionary[atom_index][subatom_index]
                        }
        
        return final_dictionary
    
    def update_with_measurement(self, measurement, atom_index: int, subatom_index: int):
        """
        Given a measurement, atom and subatom indices, update the formula tree
        """
        # add the measurement to self._measurement_dictionary
        if atom_index in self._measurement_dictionary:
            if subatom_index not in self._measurement_dictionary[atom_index]:
                self._measurement_dictionary[atom_index][subatom_index] = measurement
        else:
            self._measurement_dictionary[atom_index] = {subatom_index: measurement}
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