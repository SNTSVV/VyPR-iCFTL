"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module that holds all logic regarding binding/formula tree pairs derived while monitoring for an iCFTL specification.
"""
import logging
import datetime

from VyPR.Specifications.constraints import is_normal_atom, is_mixed_atom, get_base_variable, Conjunction, Disjunction, Negation

def milliseconds(dt):
    # thanks to https://stackoverflow.com/questions/6999726/how-can-i-convert-a-datetime-object-to-milliseconds-since-epoch-unix-time-in-p - 2021-04-12
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000.0

class FormulaTree():
    """
    Class to model a formula tree.
    
    A formula tree represents part of the current state of the monitor for an iCFTL specification.
    
    It is associated with a sequence of timestamps
    corresponding to when the concrete state/transition for each variable was observed at runtime.
    """

    def __init__(self, timestamps: list, constraint, variables: list, measurement_dictionary = None):
        """
        Store the list of timestamps that form the binding for this formula tree.
        
        Store the constraint to which the formula tree will correspond.

        Store the list of variables from the specification (in order of quantifiers).

        Store the dictionary of measurements, assuming the form
            {atom index : {subatom index : measurement}}
        """
        logging.info("Instantiating new formula tree")
        logging.info(str(measurement_dictionary))
        self._timestamps = timestamps
        self._formula_tree = constraint.instantiate()
        self._atoms = constraint.get_atomic_constraints()
        self._variables = variables
        self._measurement_dictionary = measurement_dictionary
        logging.info("  self._timestamps = %s" % str(self._timestamps))
        logging.info("  self._formula_tree = %s" % str(self._formula_tree))
        logging.info("  self._atoms = %s" % str(self._atoms))
        logging.info("  self._variables = %s" % str(self._variables))
        logging.info("  self._measurement_dictionary = %s" % str(self._measurement_dictionary))

        # run the formula tree update with respect to the measurement dictionary, if given
        if self._measurement_dictionary:
            logging.info("Updating the formula tree with respect to measurement_dictionary")
            for atom_index in self._measurement_dictionary:
                for subatom_index in self._measurement_dictionary[atom_index]:
                    measurement = self._measurement_dictionary[atom_index][subatom_index]
                    self.update_with_measurement(measurement, atom_index, subatom_index)
        else:
            self._measurement_dictionary = {}
    
    def __repr__(self):
        return f"<FormulaTree timestamps = {self._timestamps} formula tree = {self._formula_tree} observations = {self._measurement_dictionary}>"
    
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
        logging.info("Updating formula tree with measurement = %s with atom_index = %i, subatom_index = %i" % (measurement, atom_index, subatom_index))
        # if measurement is a timestamp, convert to milliseconds
        if type(measurement) is datetime.datetime:
            measurement = milliseconds(measurement)/1000.0
        # add the measurement to self._measurement_dictionary
        if atom_index in self._measurement_dictionary:
            if subatom_index not in self._measurement_dictionary[atom_index]:
                self._measurement_dictionary[atom_index][subatom_index] = measurement
        else:
            self._measurement_dictionary[atom_index] = {subatom_index: measurement}
        logging.info("Stored measurement in self._measurement_dictionary")
        # recurse on the formula tree
        # assign the result in case there is a truth value
        logging.info("Recursing on tree to update")
        self._formula_tree = self._recurse_on_tree(self._formula_tree, measurement, atom_index, subatom_index)
        logging.info("Update finished - result self._formula_tree = %s" % self._formula_tree)
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
        logging.info("Processing current_obj = %s in formula tree traversal" % str(current_obj))
        if is_normal_atom(current_obj) or is_mixed_atom(current_obj):
            logging.info("Recursive base case - found an atom")
            # base case
            # check to see whether current_obj matches atom_index
            logging.info("Checking to see if %s matches index %i" % (str(current_obj), atom_index))
            if self._atoms.index(current_obj) == atom_index:
                # return the answer given by the atom under the measurement given
                # the answer can be true, false or inconclusive (for mixed atoms)
                logging.info("current_obj = %s matches - updating with measurement = %s" % (str(current_obj), str(measurement)))
                return current_obj.check(atom_index, subatom_index, self._measurement_dictionary)
            else:
                # this isn't the atom we need, so just return it
                logging.info("No match - continuing traversal")
                return current_obj
        else:
            logging.info("Recursive case - found disjunction, conjunction or negation")
            # recursive cases
            # we either have a disjunction, conjunction or negation

            # in the disjunction case, we recurse on each disjunct and see
            # if any gives true
            if type(current_obj) is Disjunction:
                # iterate through the operands, checking whether any are evaluated to True
                disjuncts = current_obj.get_disjuncts()
                logging.info("Found disjunction - recursing on disjuncts %s" % disjuncts)
                for (index, disjunct) in enumerate(disjuncts):
                    logging.info("Processing disjunct = %s" % str(disjunct))
                    # replace the disjunct with a new value (this may just be the old value if
                    # nothing could be changed given the measurement)
                    disjuncts[index] = self._recurse_on_tree(disjunct, measurement, atom_index, subatom_index)
                    logging.info("New value for disjunct is %s" % disjunct)
                    # explicitly check for True
                    if disjuncts[index] == True:
                        logging.info("Since new value is True, and we have a disjunction, replacing disjunction with True")
                        # return True to replace current_obj with True in its parent formula
                        return True

            # in the conjunction case, we recurse on each conjunct and see
            # if any gives false
            if type(current_obj) is Conjunction:
                # iterate through the operands, checking whether any are evaluated to False
                # (or whether all are True)
                conjuncts = current_obj.get_conjuncts()
                logging.info("Found conjunction - recursing on conjuncts %s" % conjuncts)
                # count number of True occurrences so we can check for all conjuncts being true
                logging.info("Setting count of all true conjuncts to 0")
                number_of_trues = 0
                for (index, _) in enumerate(conjuncts):
                    logging.info("Processing conjunct = %s" % str(conjuncts[index]))
                    # replace the conjunct with a new value (this may just be the old value if
                    # nothing could be changed given the measurement)
                    conjuncts[index] = self._recurse_on_tree(conjuncts[index], measurement, atom_index, subatom_index)
                    logging.info("New value for conjunct is %s" % str(conjuncts[index]))
                    # explicitly check for False
                    if conjuncts[index] == False:
                        logging.info("conjuncts[index] = False in conjunction, so replacing conjunction with False")
                        # return False to replace current_obj with False in its parent formula
                        return False
                    elif conjuncts[index] == True:
                        logging.info("conjuncts[index] = True in conjunction, so incrementing the number of trues found")
                        # increase the number of Trues
                        number_of_trues += 1
                        logging.info("Number of trues/number of conjuncts = %i/%i" % (number_of_trues, len(conjuncts)))
                # check for all conjuncts being True
                if number_of_trues == len(conjuncts):
                    logging.info("Number of trues (%i) = number of conjuncts (%i), so replacing conjunction with True" % (number_of_trues, len(conjuncts)))
                    return True

            # in the negation case, we see if the operand gives a truth value
            if type(current_obj) is Negation:
                logging.info("Found negation - recursing on operand")
                # recurse on the negation operand, returning True or False if the operand gives a truth value
                current_obj.operand = self._recurse_on_tree(current_obj.operand, measurement, atom_index, subatom_index)
                logging.info("New value of negation operand is %s" % str(current_obj.operand))
                # check truth value
                if current_obj.operand == True:
                    logging.info("current_obj.operand = True, so negation becomes False")
                    # negation can be evaluated to False
                    return False
                elif current_obj.operand == False:
                    logging.info("current_obj.operand = False, so negation becomes True")
                    # negation can be evaluted to True
                    return True

            logging.info("Returning current_obj = %s to previous level of formula tree" % str(current_obj))
            return current_obj