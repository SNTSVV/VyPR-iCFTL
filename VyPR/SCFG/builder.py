"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module containing logic for construction of a symbolic control-flow graph given a Python 3 program.
"""

import ast
import datetime
import graphviz

import VyPR.Logging.logger as logger

from VyPR.Specifications.predicates import changes, calls
from VyPR.SCFG.utils import process_assignment_ast, process_expression_ast, extract_function_names, extract_symbol_names_from_target
from VyPR.SCFG.symbolic_states import (SymbolicState,
                                        EmptySymbolicState,
                                        StatementSymbolicState,
                                        ControlFlowSymbolicState,
                                        ConditionalEntrySymbolicState,
                                        ConditionalExitSymbolicState,
                                        ForLoopEntrySymbolicState,
                                        ForLoopExitSymbolicState,
                                        WhileLoopEntrySymbolicState,
                                        WhileLoopExitSymbolicState,
                                        TryEntrySymbolicState,
                                        TryExitSymbolicState)

class SCFG():

    def __init__(self, program_asts: list):
        """
        Store the list of program asts, and recursively construct the SCFG of the program given as asts.
        """
        # store asts
        self._program_asts: list = program_asts
        # initialise an empty root symbolic state
        self._root: SymbolicState = EmptySymbolicState()
        # initialise empty list of symbolic states
        self._symbolic_states: list = [self._root]
        # begin processing
        self.subprogram_to_scfg(self._program_asts, self._root)
    
    def get_root_symbolic_state(self):
        return self._root
    
    def get_symbolic_states(self):
        return self._symbolic_states
    
    def get_symbolic_states_from_symbol(self, symbol: str) -> list:
        """
        Given a predicate, determine the list of symbolic states in this SCFG that indicate a change of symbol
        """
        # filter the symbolic states to include only those that change symbol
        relevant_symbolic_states = \
            list(filter(
                lambda symbolic_state : hasattr(symbolic_state, "get_symbols_changed") and symbol in symbolic_state.get_symbols_changed(),
                self._symbolic_states
            ))
        return list(relevant_symbolic_states)
    
    def get_reachable_symbolic_states_from_symbol(self, symbol: str, symbolic_state) -> list:
        """
        Given a symbol and a symbolic state, determine the list of symbolic states in this SCFG
        that indicate a change of symbol, and that are reachable from symbolic_state.
        """
        # get all symbolic states from symbol and then filter on reachability
        relevant_symbolic_states = self.get_symbolic_states_from_symbol(symbol)
        # filter based on reachability
        relevant_symbolic_states = list(
            filter(
                lambda target_symbolic_state : self.is_reachable_from(target_symbolic_state, symbolic_state),
                relevant_symbolic_states
            )
        )
        return relevant_symbolic_states
    
    def is_reachable_from(self, target_symbolic_state, source_symbolic_state) -> bool:
        """
        Given target and source symbolic states, determine whether target
        is reachable from source.
        """
        # determine all symbolic states reachable from source_symbolic_state
        all_reachable_symbolic_states = self._get_reachable_symbolic_states(source_symbolic_state)
        # check to see if target_symbolic_state is in the list
        return target_symbolic_state in all_reachable_symbolic_states

    
    def _get_reachable_symbolic_states(self, source_symbolic_state) -> list:
        """
        Determine all symbolic states reachable from the source.
        """
        # initialise a stack
        stack = [source_symbolic_state]
        # initialise the list of visited symbolic states
        visited = [source_symbolic_state]
        # initialise the list of symbolic states reachable from source
        reachable = []
        # iterate while the stack is non-empty
        while len(stack) > 0:
            # get the top of the stack
            top = stack.pop()
            # get all children
            children = top.get_children()
            # add all unvisited children to the stack
            unvisited_children = list(
                filter(
                    lambda child: child not in visited,
                    children
                )
            )
            # add to stack
            stack += unvisited_children
            # add to reachable
            reachable += unvisited_children
            # add to visited
            visited += unvisited_children
        
        return reachable
    
    def get_next_symbolic_states(self, program_variable, base_symbolic_state) -> list:
        """
        Given a program variable and a base symbolic state, determine the symbolic states
        reachable from base_symbolic_state for which there is some path on which they are
        the first symbolic states encountered to change program_variable.

        Do this by recursively traversing the SCFG from base_symbolic_state to simulate
        the possible paths.  Each time a symbolic state is encountered that changes program_variable,
        end recursion there and add that symbolic state to a global list.
        """
        # recurse with shared lists for next and encountered
        list_of_possible_next_symbolic_states = []
        encountered = []
        self._get_next_symbolic_states(program_variable, base_symbolic_state, list_of_possible_next_symbolic_states, encountered)
        return list_of_possible_next_symbolic_states

    
    def _get_next_symbolic_states(self, program_variable, current_symbolic_state, list_of_nexts: list, encountered: list):
        """
        Recursive case for get_next_symbolic_states.
        """
        # add current_symbolic_state to encountered
        encountered.append(current_symbolic_state)
        # check to see whether current_symbolic_state changes program_variable
        if (current_symbolic_state.is_statement_symbolic_state() and
            program_variable in current_symbolic_state.get_symbols_changed()):
            # we've found a symbolic state that qualifies as next
            # add to the list of nexts, and don't recurse any further
            if current_symbolic_state not in list_of_nexts:
                list_of_nexts.append(current_symbolic_state)
        else:
            # recurse on each child
            for child in current_symbolic_state.get_children():
                if child not in encountered:
                    self._get_next_symbolic_states(program_variable, child, list_of_nexts, encountered)
            

    
    def subprogram_to_scfg(self, subprogram: list, parent_symbolic_state: SymbolicState):
        """
        Given a list of asts and a symbolic state from which the first symbolic state
        that we generate should be reachable via an edge, process each one in order to recursively
        construct a symbolic control-flow graph.
        """
        # set the previous symbolic state
        previous_symbolic_state = parent_symbolic_state
        # iterate through the current subprogram
        for subprogram_ast in subprogram:

            logger.log.info(f"Processing AST {subprogram_ast}")

            # check for the type of the current ast
            if type(subprogram_ast) in [ast.Assign, ast.Expr]:
                logger.log.info(f"AST {subprogram_ast} is {type(subprogram_ast)} instance")
                # define dictionary from ast types to the processing method to use
                ast_type_to_function = {
                    ast.Assign: process_assignment_ast,
                    ast.Expr: process_expression_ast
                }
                # instantiate the symbolic state
                new_symbolic_state: SymbolicState = ast_type_to_function[type(subprogram_ast)](subprogram_ast, subprogram)
                # add it to the list of vertices
                self._symbolic_states.append(new_symbolic_state)
                logger.log.info(f"Instantiated new_symbolic_state = {new_symbolic_state} and added to self._symbolic_states with self = {self}")
                # set it as the child of the previous
                logger.log.info(f"Calling previous_symbolic_state.add_child with previous_symbolic_state = {previous_symbolic_state} and new_symbolic_state = {new_symbolic_state}")
                previous_symbolic_state.add_child(new_symbolic_state)
                logger.log.info(f"Setting previous_symbolic_state = {new_symbolic_state}")
                previous_symbolic_state = new_symbolic_state

            
            elif type(subprogram_ast) is ast.If:
                logger.log.info(f"Type of sub_program_ast = {subprogram_ast} is ast.If")

                # deal with the main body of the conditional

                # instantiate symbolic states for entry and exit
                logger.log.info(f"Setting up conditional entry and exit symbolic states")
                entry_symbolic_state: ConditionalEntrySymbolicState = ConditionalEntrySymbolicState(subprogram_ast)
                exit_symbolic_state: ConditionalExitSymbolicState = ConditionalExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                logger.log.info(f"Entry state is entry_symbolic_state = {entry_symbolic_state} and exit state is exit_symbolic_state = {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                logger.log.info(f"Adding entry_symbolic_state = {entry_symbolic_state} as a child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)
                # recursive on the conditional body
                logger.log.info(f"Recursing on body of conditional with self._subprogram_to_scfg, linking to parent entry_symbolic_state = {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                logger.log.info(f"Setting {exit_symbolic_state} as child of final_body_symbolic_state = {final_body_symbolic_state}")
                final_body_symbolic_state.add_child(exit_symbolic_state)

                # check for orelse block
                # if there is none, set the conditional exit vertex as a child of the entry vertex
                # if there is, process it as a separate block
                logger.log.info(f"Checking for length of subprogram_ast.orelse")
                if len(subprogram_ast.orelse) != 0:
                    logger.log.info(f"An orelse block was found - recursing with parent {entry_symbolic_state}")
                    # there is an orelse block - process it
                    final_orelse_symbolic_state = self.subprogram_to_scfg(subprogram_ast.orelse, entry_symbolic_state)
                    # link final state with exit state
                    final_orelse_symbolic_state.add_child(exit_symbolic_state)
                else:
                    logger.log.info(f"No orelse block was found - adding {exit_symbolic_state} as child of {entry_symbolic_state}")
                    # there is no orelse block
                    entry_symbolic_state.add_child(exit_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            elif type(subprogram_ast) is ast.Try:
                logger.log.info(f"Type of sub_program_ast = {subprogram_ast} is ast.Try")

                # deal with the main body and the handlers

                # instantiate symbolic states for entry and exist
                logger.log.info(f"Setting up try-except entry and exit symbolic states")
                entry_symbolic_state: TryEntrySymbolicState = TryEntrySymbolicState(subprogram_ast)
                exit_symbolic_state: TryExitSymbolicState = TryExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                logger.log.info(f"Entry state is entry_symbolic_state = {entry_symbolic_state} and exit state is exit_symbolic_state = {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                logger.log.info(f"Adding entry_symbolic_state = {entry_symbolic_state} as a child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)

                # recurse on the main body
                logger.log.info(f"Recursing on body of try-except with self._subprogram_to_scfg, linking to parent entry_symbolic_state = {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                logger.log.info(f"Setting {exit_symbolic_state} as child of final_body_symbolic_state = {final_body_symbolic_state}")
                final_body_symbolic_state.add_child(exit_symbolic_state)

                # recurse on each handler
                for handler in subprogram_ast.handlers:
                    logger.log.info(f"Recursing on handler of try-except with self._subprogram_to_scfg, linking to parent entry_symbolic_state = {entry_symbolic_state}")
                    final_body_symbolic_state = self.subprogram_to_scfg(handler.body, entry_symbolic_state)
                    # set the exist symbolic state as a child of the final one from the body
                    logger.log.info(f"Setting {exit_symbolic_state} as child of final_body_symbolic_state = {final_body_symbolic_state}")
                    final_body_symbolic_state.add_child(exit_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            elif type(subprogram_ast) is ast.For:
                logger.log.info(f"Type of subprogram_ast = {subprogram_ast} is ast.For")

                # deal with the body of the for loop

                # instantiate symbolic states for entry and exit
                logger.log.info(f"Setting up for-loop entry and exit symbolic states")
                # derive the list of names of program variables used as loop counters
                loop_counter_variables = extract_symbol_names_from_target(subprogram_ast.target)
                logger.log.info(f"Loop counter variables used by the loop are {loop_counter_variables}")
                # instantiate states
                entry_symbolic_state: ForLoopEntrySymbolicState = ForLoopEntrySymbolicState(loop_counter_variables, subprogram_ast)
                exit_symbolic_state: ForLoopExitSymbolicState = ForLoopExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                logger.log.info(f"Entry state is entry_symbolic_state = {entry_symbolic_state} and exit state is exit_symbolic_state = {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                logger.log.info(f"Adding entry_symbolic_state = {entry_symbolic_state} as a child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)
                # recursive on the loop body
                logger.log.info(f"Recursing on body of loop, linking to parent {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                logger.log.info(f"Setting exit_symbolic_state = {exit_symbolic_state} as child of block")
                final_body_symbolic_state.add_child(exit_symbolic_state)
                # set for loop entry symbolic state as child of final state in body
                logger.log.info(f"Setting entry symbolic state entry_symbolic_state = {entry_symbolic_state} as child of final state {final_body_symbolic_state}")
                final_body_symbolic_state.add_child(entry_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            elif type(subprogram_ast) is ast.While:
                logger.log.info(f"Type of subprogram_ast = {subprogram_ast} is ast.While")

                # deal with the body of the while loop

                # instantiate symbolic states while entry and exit
                logger.log.info(f"Setting up while-loop entry and exit symbolic states")
                # instantiate states
                entry_symbolic_state: WhileLoopEntrySymbolicState = WhileLoopEntrySymbolicState(subprogram_ast)
                exit_symbolic_state: WhileLoopExitSymbolicState = WhileLoopExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                logger.log.info(f"Entry state is entry_symbolic_state = {entry_symbolic_state} and exit state is exit_symbolic_state = {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                logger.log.info(f"Adding entry_symbolic_state = {entry_symbolic_state} as a child of previous_symbolic_state = {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)
                # recursive on the loop body
                logger.log.info(f"Recursing on body of loop, linking to parent {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                logger.log.info(f"Setting exit_symbolic_state = {exit_symbolic_state} as child of block")
                final_body_symbolic_state.add_child(exit_symbolic_state)
                # set for loop entry symbolic state as child of final state in body
                logger.log.info(f"Setting entry symbolic state entry_symbolic_state = {entry_symbolic_state} as child of final state final_body_symbolic_state = {final_body_symbolic_state}")
                final_body_symbolic_state.add_child(entry_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            logger.log.info(f"Moving to next iteration with previous_symbolic_state = {previous_symbolic_state}")
        
        # return the final symbolic state from this subprogram
        return previous_symbolic_state

    
    def write_to_file(self, filename: str):
        """
        Write a dot file of the SCFG.
        """
        logger.log.info(f"Writing graph filename = {filename} for SCFG.")
        # instantiate directed graph
        graph = graphviz.Digraph()
        graph.attr("graph", splines="true", fontsize="10")
        shape = "rectangle"
        # iterate through symbolic states, draw edges between those that are linked
        # by child/parent
        for symbolic_state in self._symbolic_states:
            logger.log.info(f"Processing symbolic_state = {symbolic_state}")
            if type(symbolic_state) is StatementSymbolicState:
                graph.node(str(id(symbolic_state)), str(symbolic_state.get_symbols_changed()), shape=shape)
            elif type(symbolic_state) is ForLoopEntrySymbolicState:
                graph.node(str(id(symbolic_state)), f"{type(symbolic_state).__name__} : {symbolic_state.get_symbols_changed()}", shape=shape)
            else:
                graph.node(str(id(symbolic_state)), type(symbolic_state).__name__, shape=shape)
            for child in symbolic_state.get_children():
                graph.edge(
                    str(id(symbolic_state)),
                    str(id(child))
                )
        graph.render(filename)
        logger.log.info(f"SCFG written to file {filename}")