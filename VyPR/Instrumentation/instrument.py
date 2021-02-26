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
from VyPR.Specifications.constraints import Constraint, ConcreteStateVariable, TransitionVariable
from VyPR.Instrumentation.prepare import prepare_specification
from VyPR.SCFG.prepare import construct_scfg_of_function
from VyPR.SCFG.search import SCFGSearcher

class Analyser():
    """
    Class for static analysis of source code based on an iCFTL specification.
    """

    def __init__(self, specification_file, root_directory):
        """
        Store the specification and function -> scfg map for use in other methods.

        root_directory is the directory with respect to which fully-qualified function names
        are defined.
        """
        # import specification from the file given
        self._specification = prepare_specification(specification_file)

        # get the list of functions referred to in the specification
        self._all_functions = self._specification.get_function_names_used()

        # get the scfg of each of these functions
        self._function_name_to_scfg_map = {}
        # iterate through the list of functions
        for function in self._all_functions:
            self._function_name_to_scfg_map[function] = construct_scfg_of_function(function)
        
        # initialise SCFGSearcher instance
        self._scfg_searcher = SCFGSearcher(self._function_name_to_scfg_map)
    
    def compute_instrumentation_points(self) -> list:
        """
        Inspect the specification's quantifiers and constraint in order to compute
        the list of symbolic states/pairs of symbolic states at which instrumentation
        must be applied.

        Each instrumentation point should be a dictionary containing a type and various
        data useful for the instrumentation code that will be placed.
        """
        # compute the set of maps generated by quantifiers
        maps_from_quantifiers = self.inspect_quantifiers()

        # based on these maps, compute a map (binding index, atom index) -> set of symbolic states/pairs
        # of intrumentation points
    
    def inspect_quantifiers(self) -> list:
        """
        Traverse the specification in order to determine the sequence of (variable, predicate)
        pairs.
        
        Store this sequence under self._quantifier_pair_sequence.

        Then, for each pair, use the predicate to identify relevant concrete states/pairs of concrete states
        and associate those with the variables.

        Since each quantifier depends on the previous in iCFTL, we construct the maps recursively.
        """
        # initialise an empty list of pairs (variable, predicate)
        variable_predicate_pairs = []
        # set the current object to be the top-level specification
        current_obj = self._specification
        # iterate through the structure, using the type Constraint as a place to stop
        while type(current_obj) is not Constraint:
            # traverse depending on the type of the current object
            if type(current_obj) is Specification:
                current_obj = current_obj.get_quantifier()
            elif type(current_obj) is Forall:
                # first, add to the map
                # we check the type of the predicate so we know what kind of variable to instantiate
                variable_predicate_pairs.append([current_obj.get_variable(), current_obj.get_predicate()])
                # in the case of a quantifier, the two possibilities are
                # that the next item to consider is a quantifier or a constraint
                if current_obj.get_quantifier():
                    current_obj = current_obj.get_quantifier()
                else:
                    # if we arrive at a constraint, the loop
                    # will stop at the next ieration
                    current_obj = current_obj.get_constraint()
        
        # store the sequence we just constructed
        self._quantifier_pair_sequence = variable_predicate_pairs

        # recursively construct the set of lists based on this quantifier sequence
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

    
    def _recurse_on_quantifier(self, index_to_process=0, current_list=[]):
        """
        Determine which symbolic states satisfy the predicate at index_to_process,
        extend current_list using each of these and, for each new list (if not complete), recurse.
        When done, return the set of new maps generated.
        """
        # get the predicate
        predicate = self._quantifier_pair_sequence[index_to_process][1]
        # get the final symbolic state from current_list (can be None if current_list = [])
        if current_list == []:
            previous_symbolic_state = None
        else:
            previous_symbolic_state = current_list[-1]
        # get the relevant symbolic states based on this predicate
        # this involves determining the relevant scfg and then the symbolic states
        relevant_symbolic_states = self._scfg_searcher.find_symbolic_states(predicate, previous_symbolic_state)
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

        # recursive base case - index_to_process indicates the final quantifier
        if index_to_process == len(self._quantifier_pair_sequence)-1:
            lists_to_return = extended_lists

        # recursive case - index_to_process does not indicate the final quantifier,
        # so we have to recurse further based on new entries that are identified
        if index_to_process < len(self._quantifier_pair_sequence)-1:
            # initialise empty list of results from recursion
            recursed_lists = []
            # iterate through extended lists, recurse on them and add results to recursed_lists
            for extended_list in extended_lists:
                # recurse
                new_lists = self._recurse_on_quantifier(index_to_process+1, extended_list)
                # add to list of recursed lists
                recursed_lists += new_lists
            lists_to_return = recursed_lists
        
        return lists_to_return