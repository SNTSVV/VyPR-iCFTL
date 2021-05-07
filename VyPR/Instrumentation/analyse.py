"""
Main module to handle logic for instrumentation.

Instrumentation consists of generating an instance of the Analyser class.

The purpose of the Analyser class is to perform the static analysis
necessary to determine from where in the monitored code base measurements should be taken
at runtime in order to check the iCFTL specification given.

The Analyser class take a VyPR.Specifications.builder.Specification instance
and a map from fully-qualified function names to the corresponding
VyPR.SCFG.builder.SCFG instances.

From here, the quantifiers are inspected (by traversal from the specification root
until the constraint) to determine the sequence of variables/predicates to use.

This process generates a set of maps from variables to symbolic states/pairs of symbolic states
in the set of SCFGs.

Based on these maps, the constraint part of the specification is then inspected
to determine the additional symbolic states/pairs of symbolic states that are needed.
"""

from VyPR.Specifications.builder import Specification, Forall
from VyPR.Specifications.constraints import Constraint
from VyPR.SCFG.search import SCFGSearcher
import VyPR.Logging.logger as logger

class Analyser():
    """
    Class for static analysis of source code based on an iCFTL specification.
    """

    def __init__(self, specification, function_name_to_scfg_map):
        """
        Store the specification and function -> scfg map for use in other methods.
        """
        # store specification
        self._specification = specification
        logger.log.info(f"Specification is\n{self._specification}")

        # initialise the map from function names to SCFGs
        self._function_name_to_scfg_map = function_name_to_scfg_map
        
        # initialise SCFGSearcher instance using the function name -> SCFG map
        logger.log.info("Initialising a SCFGSearcher instance for the symbolic control-flow graphs")
        self._scfg_searcher = SCFGSearcher(function_name_to_scfg_map)
    
    def get_scfg_searcher(self):
        return self._scfg_searcher
    
    def compute_instrumentation_points(self) -> list:
        """
        Inspect the specification's quantifiers and constraint in order to compute
        the list of symbolic states/pairs of symbolic states at which instrumentation
        must be applied.

        Each instrumentation point should be a dictionary containing a type and various
        data useful for the instrumentation code that will be placed.

        Return the list of maps from variables to symbolic states (derived from quantifiers)
        and the tree of instrumentation points.
        """
        # compute the set of maps generated by quantifiers
        logger.log.info("Calling self._inspect_quantifiers to inspect quantifier sequence")
        variable_to_symbolic_state_maps = self._inspect_quantifiers()

        # based on these maps, compute a map (binding index, atom index, subatom index) -> list of symbolic states
        # of intrumentation points
        logger.log.info("Calling self._inspect_constraints() given statements identified by quantifiers")
        instrumentation_point_map = self._inspect_constraints(variable_to_symbolic_state_maps)

        return variable_to_symbolic_state_maps, instrumentation_point_map
    
    def _inspect_quantifiers(self) -> list:
        """
        Traverse the specification in order to determine the sequence of (variable, predicate)
        pairs.
        
        Store this sequence under self._quantifier_pair_sequence.

        Then, for each pair, use the predicate to identify relevant concrete states/pairs of concrete states
        and associate those with the variables.

        Since each quantifier depends on the previous in iCFTL, we construct the maps recursively.
        """
        logger.log.info("Computing (variable, predicate) sequence from quantifiers")
        # initialise an empty list of pairs (variable, predicate)
        variable_predicate_pairs = []
        # set the current object to be the top-level specification
        current_obj = self._specification
        logger.log.info(f"Continuing traversal with current_obj = {current_obj}")
        # iterate through the structure, using the type Constraint as a place to stop
        while type(current_obj) is not Constraint:
            logger.log.info(f"Continuing traversal with current_obj = {current_obj}")
            # traverse depending on the type of the current object
            if type(current_obj) is Specification:
                current_obj = current_obj.get_quantifier()
            elif type(current_obj) is Forall:
                logger.log.info("Encountered Forall instance")
                # first, add to the map
                # we check the type of the predicate so we know what kind of variable to instantiate
                logger.log.info(f"Adding {[current_obj.get_variable(), current_obj.get_predicate()]} to variable_predicate_pairs")
                variable_predicate_pairs.append([current_obj.get_variable(), current_obj.get_predicate()])
                # in the case of a quantifier, the two possibilities are
                # that the next item to consider is a quantifier or a constraint
                if current_obj.get_quantifier():
                    current_obj = current_obj.get_quantifier()
                else:
                    # if we arrive at a constraint, the loop
                    # will stop at the next ieration
                    current_obj = current_obj.get_constraint()
        
        logger.log.info(f"variable_predicate_pairs = {variable_predicate_pairs}")
        
        # store the sequence we just constructed
        self._quantifier_pair_sequence = variable_predicate_pairs

        # recursively construct the set of lists based on this quantifier sequence
        logger.log.info("Calling self._recurse_on_quantifier to extract key statements from source code based on self._quantifier_pair_sequence")
        lists = self._recurse_on_quantifier()

        # initialise empty list of dictionaries to be derived from lists
        variable_to_symbolic_state_maps = []
        # transform lists to dictionaries
        for symbolic_state_list in lists:
            # initialise empty dictionary
            new_map = {}
            # iterate through the quantifier pair sequence and the list at the same time
            # in order to build up a dictionary
            for i in range(len(self._quantifier_pair_sequence)):
                new_map[self._quantifier_pair_sequence[i][0]] = symbolic_state_list[i]
            # append the new map
            variable_to_symbolic_state_maps.append(new_map)
        
        logger.log.info(f"variable_to_symbolic_state_maps = {variable_to_symbolic_state_maps}")
        
        return variable_to_symbolic_state_maps

    
    def _recurse_on_quantifier(self, index_to_process=0, current_list=[]):
        """
        Determine which symbolic states satisfy the predicate at index_to_process,
        extend current_list using each of these and, for each new list (if not complete), recurse.
        When done, return the set of new maps generated.
        """
        logger.log.info(f"index_to_process = {index_to_process}")
        logger.log.info(f"current_list = {current_list}")
        # get the predicate
        predicate = self._quantifier_pair_sequence[index_to_process][1]
        logger.log.info(f"Will determine key statements based on predicate {predicate}")
        # get the final symbolic state from current_list (can be None if current_list = [])
        if current_list == []:
            previous_symbolic_state = None
        else:
            previous_symbolic_state = current_list[-1]
        logger.log.info(f"previous_symbolic_state = {previous_symbolic_state}")
        # get the relevant symbolic states based on this predicate
        # this involves determining the relevant scfg and then the symbolic states
        relevant_symbolic_states = self._scfg_searcher.find_symbolic_states(predicate, previous_symbolic_state)
        logger.log.info(f"relevant_symbolic_states = {relevant_symbolic_states}")
        # initialise an empty list of extended lists
        extended_lists = []
        # construct an extension of current_map for each symbolic state that we found
        for symbolic_state in relevant_symbolic_states:
            # copy list
            extended_list = [e for e in current_list]
            # extend
            extended_list.append(symbolic_state)
            # add to the list
            extended_lists.append(extended_list)
        logger.log.info(f"extended_lists = {extended_lists}")

        # recursive base case - index_to_process indicates the final quantifier
        if index_to_process == len(self._quantifier_pair_sequence)-1:
            lists_to_return = extended_lists

        # recursive case - index_to_process does not indicate the final quantifier,
        # so we have to recurse further based on new entries that are identified
        if index_to_process < len(self._quantifier_pair_sequence)-1:
            logger.log.info("index_to_process < 1 - recursing...")
            # initialise empty list of results from recursion
            recursed_lists = []
            # iterate through extended lists, recurse on them and add results to recursed_lists
            for extended_list in extended_lists:
                logger.log.info(f"Recursing on extended_list = {extended_list}")
                # recurse
                new_lists = self._recurse_on_quantifier(index_to_process+1, extended_list)
                logger.log.info(f"From recursion, new_lists = {new_lists}")
                # add to list of recursed lists
                recursed_lists += new_lists
            lists_to_return = recursed_lists
        
        logger.log.info(f"Key statements identified by quantifier, lists_to_return = {lists_to_return}")
        
        return lists_to_return
    
    def _inspect_constraints(self, variable_to_symbolic_state_maps) -> dict:
        """
        For each map in variable_to_symbolic_state_maps, use the constraint part of the
        specification to determine the points from which data must be taken.

        To do this, iterate through the maps in variable_to_symbolic_state_maps and, for each one,
        iterate through the atomic constraints and use each one to find a list of symbolic states.

        The end result should be a map:
        
        (index of (variable -> symbolic state) map) -> (index of atomic constraint)
            -> (index of sub-atomic constraint) -> list of instrumentation points
        """
        logger.log.info("Beginning inspection of constraints")
        # initialise empty map for final lists of instrumentation points
        instrumentation_point_tree = {}
        # get the constraint part of the specification
        constraint = self._specification.get_constraint()
        logger.log.info(f"constraint = {constraint}")
        # get the atomic constraints
        atomic_constraints = constraint.get_atomic_constraints()
        logger.log.info(f"atomic_constraints = {atomic_constraints}")
        # iterate through the maps
        for (map_index, variable_to_symbolic_state_map) in enumerate(variable_to_symbolic_state_maps):
            logger.log.info(f"Processing map_index = {map_index}")
            # initialise map for this map index
            instrumentation_point_tree[map_index] = {}
            # iterate through the atomic constraints
            for (atomic_constraint_index, atomic_constraint) in enumerate(atomic_constraints):
                logger.log.info(f"Processing atomic_constraint_index = {atomic_constraint_index}")
                # construct this entry of the map
                instrumentation_point_tree[map_index][atomic_constraint_index] = \
                    self._scfg_searcher.get_instrumentation_points_for_atomic_constraint(
                        atomic_constraint,
                        variable_to_symbolic_state_map
                    )
                logger.log.info(
                    f"map_index = {map_index}, atomic_constraint_index = {atomic_constraint_index} gave "\
                        f"key statements {instrumentation_point_tree[map_index][atomic_constraint_index]}"
                )

        return instrumentation_point_tree