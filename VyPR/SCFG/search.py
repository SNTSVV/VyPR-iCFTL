"""
Module to hold all logic for searching a set of SCFGs for symbolic state/pairs of symbolic states
based on a predicate found in an iCFTL specification.
"""

from VyPR.Specifications.predicates import changes, calls, future

class SCFGSearcher():
    """
    Class to represent a map from function names to SCFGs, and then provide
    methods to determine the set of symbolic states
    that satisfy a given predicate from an iCFTL specification.
    """

    def __init__(self, function_name_to_scfg_map):
        """
        Store the function_scfg_map for later.
        """
        self._function_name_to_scfg_map = function_name_to_scfg_map
    
    def find_symbolic_states(self, predicate, base_symbolic_state):
        """
        Given a predicate (and, in the case of future, a base symbolic state),
        find the relevant symbolic states.
        """
        # check the type of the predicate
        if type(predicate) in [changes, calls]:
            # get the program symbol
            if type(predicate) is changes:
                program_variable = predicate.get_program_variable()
            else:
                program_variable = predicate.get_function_name()
            # get the function at whose SCFG we will look
            function_name = predicate.get_during_function()
            # get the relevant SCFG
            relevant_scfg = self._function_name_to_scfg_map[function_name]
            # get the relevant symbolic states
            relevant_symbolic_states = relevant_scfg.get_symbolic_states_from_symbol(program_variable)
        elif type(predicate) is future:
            # find all symbolic state matching the predicate
            # with the additional constraint that they must be reachable from previous_symbolic_state
            # get the predicate
            inner_predicate = predicate.get_predicate()
            # get the program symbol
            if type(predicate) is changes:
                program_variable = inner_predicate.get_program_variable()
            else:
                program_variable = inner_predicate.get_function_name()
            # get the function at whose SCFG we will look
            function_name = inner_predicate.get_during_function()
            # get the relevant SCFG
            relevant_scfg = self._function_name_to_scfg_map[function_name]
            # if function_name is different from the function inside which base_symbolic_state
            # is found, we don't need to look at reachability - we just get all relevant
            # symbolic states
            base_function_name = self.get_function_name_of_symbolic_state(base_symbolic_state)
            if function_name == base_function_name:
                # consider reachability
                # since we're looking for a symbolic state in the same SCFG,
                # get the relevant symbolic states reachable from base_symbolic_state
                relevant_symbolic_states = relevant_scfg.get_reachable_symbolic_states_from_symbol(
                    program_variable,
                    base_symbolic_state
                )
            else:
                # don't consider reachability, since we're looking for a symbolic state in another SCFG
                relevant_symbolic_states = relevant_scfg.get_symbolic_states_from_symbol(program_variable)
        
        return relevant_symbolic_states
    
    def get_function_name_of_symbolic_state(self, symbolic_state) -> str:
        """
        Given a symbolic state, search through self._function_name_to_scfg_map
        and return the name of the function whose SCFG contains the symbolic state.
        """
        # iterate through the function -> scfg map
        for function_name in self._function_name_to_scfg_map:
            # check whether symbolic_state is contained by the corresponding SCFG
            scfg = self._function_name_to_scfg_map[function_name]
            symbolic_states = scfg.get_symbolic_states()
            # there must be an SCFG containing the symbolic state we're searching for
            # this function cannot return None
            if symbolic_state in symbolic_states:
                return function_name