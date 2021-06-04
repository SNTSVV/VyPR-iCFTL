"""
Module to hold all logic for searching a set of SCFGs for symbolic state/pairs of symbolic states
based on a predicate found in an iCFTL specification.
"""

from VyPR.Specifications.predicates import changes, calls, future
from VyPR.Specifications.constraints import (ValueInConcreteStateEqualsConstant,
                                            ValueInConcreteStateLessThanConstant,
                                            ValueInConcreteStateGreaterThanConstant,
                                            DurationOfTransitionLessThanConstant,
                                            DurationOfTransitionGreaterThanConstant,
                                            TimeBetweenLessThanConstant,
                                            NextTransitionFromConcreteState,
                                            NextConcreteStateFromConcreteState,
                                            NextTransitionFromTransition,
                                            NextConcreteStateFromTransition,
                                            ConcreteStateAfterTransition,
                                            ConcreteStateBeforeTransition,
                                            derive_sequence_of_temporal_operators)
import VyPR.Logging.logger as logger

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
        logger.log.info(f"Finding symbolic states satisfying predicate {predicate} based on {base_symbolic_state}")
        # check the type of the predicate
        if type(predicate) in [changes, calls]:
            # get the program symbol
            if type(predicate) is changes:
                program_variable = predicate.get_program_variable()
            else:
                program_variable = predicate.get_function_name()
            logger.log.info(f"Looking for symbolic states changing the program variable {program_variable}")
            # get the function at whose SCFG we will look
            function_name = predicate.get_during_function()
            # get the relevant SCFG
            logger.log.info(f"Getting symbolic control-flow graph for function '{function_name}'")
            relevant_scfg = self._function_name_to_scfg_map[function_name]
            # get the relevant symbolic states
            logger.log.info(f"Getting symbolic states that change the program variable '{program_variable}'")
            relevant_symbolic_states = relevant_scfg.get_symbolic_states_from_symbol(program_variable)
        elif type(predicate) is future:
            # find all symbolic state matching the predicate
            # with the additional constraint that they must be reachable from previous_symbolic_state
            # get the predicate
            inner_predicate = predicate.get_predicate()
            logger.log.info(f"Inner predicate used by future is {inner_predicate}")
            # get the program symbol
            if type(inner_predicate) is changes:
                program_variable = inner_predicate.get_program_variable()
            else:
                program_variable = inner_predicate.get_function_name()
            logger.log.info(f"Looking for symbolic states changing the program variable {program_variable}")
            # get the function at whose SCFG we will look
            function_name = inner_predicate.get_during_function()
            # get the relevant SCFG
            logger.log.info(f"Getting symbolic control-flow graph for function '{function_name}'")
            relevant_scfg = self._function_name_to_scfg_map[function_name]
            # if function_name is different from the function inside which base_symbolic_state
            # is found, we don't need to look at reachability - we just get all relevant
            # symbolic states
            logger.log.info(f"Getting function to which symbolic state {base_symbolic_state} belongs")
            base_function_name = self.get_function_name_of_symbolic_state(base_symbolic_state)
            logger.log.info(f"Function to which symbolic state {base_symbolic_state} belongs is {base_function_name}")
            if function_name == base_function_name:
                logger.log.info("future predicate refers to the same function - searching forward in SCFG")
                # consider reachability
                # since we're looking for a symbolic state in the same SCFG,
                # get the relevant symbolic states reachable from base_symbolic_state
                relevant_symbolic_states = relevant_scfg.get_reachable_symbolic_states_from_symbol(
                    program_variable,
                    base_symbolic_state
                )
            else:
                logger.log.info("future predicate refers to a different function - searching whole SCFG")
                # don't consider reachability, since we're looking for a symbolic state in another SCFG
                relevant_symbolic_states = relevant_scfg.get_symbolic_states_from_symbol(program_variable)
        
        logger.log.info(f"Symbolic states found for predicate {predicate} are {relevant_symbolic_states}")
        
        return relevant_symbolic_states
    
    def get_symbolic_states_from_temporal_operator(self, temporal_operator, base_symbolic_state) -> list:
        """
        Given a temporal operator object and a base symbolic state, either traverse
        forwards in the current symbolic control-flow graph, or search in others to determine the list of
        relevant symbolic states.
        """
        # check the type of the temporal operator
        if type(temporal_operator) in [NextConcreteStateFromConcreteState,
                                        NextTransitionFromConcreteState,
                                        NextConcreteStateFromTransition,
                                        NextTransitionFromTransition]:
            # we have a Next... operator, so we have two options:
            # 1) if the function in the predicate matches the function containing base_symbolic_state,
            #    we search forwards in that function's SCFG for appropriate symbolic states, or
            # 2) if the function in the predicate differs from the function containign base_symbolic_state,
            #    we search everywhere in the other function's SCFG (no reachability constraints).

            # get the function name of base_symbolic_state
            base_function_name = self.get_function_name_of_symbolic_state(base_symbolic_state)
            # get the function name from the predicate in temporal_operator
            temporal_operator_function_name = temporal_operator.get_predicate().get_during_function()
            # get the program variable from the temporal operator's predicate
            temporal_operator_predicate = temporal_operator.get_predicate()
            if type(temporal_operator_predicate) is changes:
                program_variable = temporal_operator_predicate.get_program_variable()
            else:
                program_variable = temporal_operator_predicate.get_function_name()
            # check for equality
            if base_function_name == temporal_operator_function_name:
                # get the relevant SCFG
                relevant_scfg = self._function_name_to_scfg_map[base_function_name]
                # the functions are equal, so we traverse forwards in the relevant SCFG
                relevant_symbolic_states = \
                    relevant_scfg.get_next_symbolic_states(
                        program_variable,
                        base_symbolic_state
                    )
            else:
                # the functions are not equal, so we get relevant symbolic states without looking
                # at reachability
                # get the relevant SCFG
                relevant_scfg = self._function_name_to_scfg_map[temporal_operator_function_name]
                # get rlevant symbolic states
                relevant_symbolic_states = relevant_scfg.get_symbolic_states_from_symbol(program_variable)
        
        elif type(temporal_operator) is ConcreteStateAfterTransition:
            # since we represent edges with the symbolic states immediately after them,
            # here we can just return base_symbolic_state
            relevant_symbolic_states = [base_symbolic_state]

        elif type(temporal_operator) is ConcreteStateBeforeTransition:
            # we get the same symbolic state as in the ConcreteStateBeforeTransition case - we leave it to
            # the final instrument placement to adjust indices accordingly
            relevant_symbolic_states = [base_symbolic_state]
        
        return relevant_symbolic_states
    
    def get_function_name_of_symbolic_state(self, symbolic_state) -> str:
        """
        Given a symbolic state, search through self._function_name_to_scfg_map
        and return the name of the function whose SCFG contains the symbolic state.
        """
        logger.log.info(f"Determining function that generated symbolic state {symbolic_state}")
        # iterate through the function -> scfg map
        for function_name in self._function_name_to_scfg_map:
            # check whether symbolic_state is contained by the corresponding SCFG
            scfg = self._function_name_to_scfg_map[function_name]
            symbolic_states = scfg.get_symbolic_states()
            # there must be an SCFG containing the symbolic state we're searching for
            # this function cannot return None
            if symbolic_state in symbolic_states:
                logger.log.info(f"Found symbolic state in function '{function_name}'")
                return function_name
    
    def get_instrumentation_points_for_atomic_constraint(self, atomic_constraint, variable_symbolic_state_map: dict) -> dict:
        """
        Given an atomic constraint and a map from variables to symbolic states,
        determine the map from sub-atom indices to lists of symbolic states that are relevant to that part of the constraint.
        """
        # initialise the empty map
        subatom_index_to_symbolic_states = {}
        # get the map of sequences of temporal operators for the atomic constraint given
        temporal_operator_sequence_map = derive_sequence_of_temporal_operators(atomic_constraint)
        # for each sequence of temporal operators (1 for normal atoms, 2 for mixed atoms),
        # determine the appropriate list of symbolic states
        for subatom_index in temporal_operator_sequence_map:
            # initialise subatom_index_to_symbolic_states for this subatom index
            subatom_index_to_symbolic_states[subatom_index] = []
            # get the sequence of temporal operators and base variable for this subatom index
            base_variable = temporal_operator_sequence_map[subatom_index][-1]
            temporal_operator_sequence = temporal_operator_sequence_map[subatom_index][:-1]
            # based on this sequence, determine the list of symbolic states (by determining the symbolic states identified by each
            # temporal operator in the sequence)
            # to do this, iterate through the temporal operators in the sequence, each time replacing the current list
            # of symbolic states

            # initialise empty list of symbolic state
            # using base_variable to get the relevant symbolic state from variable_symbolic_state_map
            current_symbolic_states = [variable_symbolic_state_map[base_variable.get_name()]]
            # iterate through the list of temporal operators
            for temporal_operator in temporal_operator_sequence:
                # for each symbolic state in current_symbolic_states, determine the relevant next
                # symbolic state based on temporal_operator

                # initialise empty list of symbolic states from the next stage of traversal
                new_symbolic_states = []
                # iterate through current_symbolic_states
                for current_symbolic_state in current_symbolic_states:
                    # get the list of next ones based on temporal_operator
                    next_symbolic_states = self.get_symbolic_states_from_temporal_operator(
                        temporal_operator,
                        current_symbolic_state
                    )
                    # add to new_symbolic_states
                    new_symbolic_states += next_symbolic_states
                
                # overwrite current_symbolic_states
                current_symbolic_states = new_symbolic_states
            
            # add current_symbolic_states to the subatom index map
            subatom_index_to_symbolic_states[subatom_index] = current_symbolic_states

        return subatom_index_to_symbolic_states