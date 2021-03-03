"""
Module containing logic for construction of a symbolic control-flow graph given a Python 3 program.
"""

import ast
import datetime
import graphviz

from VyPR.Specifications.predicates import changes, calls
import VyPR.Logging.logger as logger

class SymbolicState():
    """
    Base class for all types of symbolic states.
    """

    def __init__(self):
        self._children: list = []
        self._parents: list = []
    
    def __repr__(self):
        return f"<{type(self).__name__} (id {id(self)})>"
    
    def is_statement_symbolic_state(self):
        return type(self) is StatementSymbolicState
    
    def add_child(self, child_symbolic_state):
        """
        Add a child symbolic state to self.
        """
        logger.log.info(f"Appending child_symbolic_state = {child_symbolic_state} to self._children with self = {self}")
        self._children.append(child_symbolic_state)
        # also set self as parent of child
        logger.log.info(f"Also calling child_symbolic_state.add_parent to add self = {self} as parent of child_symbolic_state = {child_symbolic_state}")
        child_symbolic_state.add_parent(self)
    
    def add_parent(self, parent_symbolic_state):
        """
        Add a parent symbolic state to self.
        """
        logger.log.info(f"Appending parent_symbolic_state = {parent_symbolic_state} to self._parents with self = {self}")
        self._parents.append(parent_symbolic_state)
    
    def get_children(self) -> list:
        return self._children
    
    def get_parents(self) -> list:
        return self._parents

class EmptySymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the root for any symbolic control-flow graph.
    """
    def __init__(self):
        super().__init__()

class StatementSymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the state induced by a normal statement
    (such as an assignment or a function call).
    """
    def __init__(self, symbols_changed: list, ast_obj):
        super().__init__()
        self._symbols_changed = symbols_changed
        self._ast_obj = ast_obj
    
    def __repr__(self):
        return f"<SymbolicState (id {id(self)}, changes {self._symbols_changed})>"
    
    def get_symbols_changed(self) -> list:
        return self._symbols_changed
    
    def get_ast_object(self):
        return self._ast_obj

class ControlFlowSymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the base class for all symbolic states
    representing control-flow.
    """
    def __init__(self):
        super().__init__()

class ConditionalEntrySymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for conditionals.
    """
    def __init__(self, ast_obj):
        super().__init__()
        self._ast_obj = ast_obj

class ConditionalExitSymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for conditionals.
    """
    def __init__(self):
        super().__init__()

class ForLoopEntrySymbolicState(StatementSymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for for-loops.

    The constructor takes the name of the iterator used by the for loop.
    """
    def __init__(self, loop_counter_variables, ast_obj):
        super().__init__(loop_counter_variables, ast_obj)
        self._ast_obj = ast_obj

class ForLoopExitSymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for for-loops.
    """
    def __init__(self):
        super().__init__()

class WhileLoopEntrySymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for while-loops.
    """
    def __init__(self, ast_obj):
        super().__init__()
        self._ast_obj = ast_obj

class WhileLoopExitSymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for while-loops.
    """
    def __init__(self):
        super().__init__()

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
        # recurse with shared list
        list_of_possible_next_symbolic_states = []
        self._get_next_symbolic_states(program_variable, base_symbolic_state, list_of_possible_next_symbolic_states)
        return list_of_possible_next_symbolic_states

    
    def _get_next_symbolic_states(self, program_variable, current_symbolic_state, list_of_nexts: list):
        """
        Recursive case for get_next_symbolic_states.
        """
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
                self._get_next_symbolic_states(program_variable, child, list_of_nexts)
            

    
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
                    ast.Assign: self._process_assignment_ast,
                    ast.Expr: self._process_expression_ast
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
            
            elif type(subprogram_ast) is ast.For:
                logger.log.info(f"Type of subprogram_ast = {subprogram_ast} is ast.For")

                # deal with the body of the for loop

                # instantiate symbolic states for entry and exit
                logger.log.info(f"Setting up for-loop entry and exit symbolic states")
                # derive the list of names of program variables used as loop counters
                loop_counter_variables = self._extract_symbol_names_from_target(subprogram_ast.target)
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
    
    def _process_assignment_ast(self, stmt_ast: ast.Assign, stmt_ast_parent_block):
        """
        Instantiate a new SymbolicState instance based on this assignment statement.

        The target program variables, along with any functions called on the right-hand-side
        of the assignment, will be included as symbols changed by that Symbolic State
        """
        # first, add a reference from stmt_ast to its parent block
        stmt_ast.parent_block = stmt_ast_parent_block
        logger.log.info(f"Instantiating symbolic state for AST instance stmt_ast = {stmt_ast}")
        # determine the program variables assigned on the left-hand-side
        targets: list = stmt_ast.targets
        # extract names - for now just care about normal program variables, not attributes or functions
        target_names: list = []
        for target in targets:
            target_names += self._extract_symbol_names_from_target(target)
        logger.log.info(f"List of all program variables changed is {target_names}")
        # extract function names
        assigned_value = stmt_ast.value
        function_names: list = self._extract_function_names(assigned_value)
        logger.log.info(f"List of all program functions called is {function_names}")
        # merge the two lists of symbols
        all_symbols: list = target_names + function_names
        logger.log.info(f"List of all symbols to mark as changed in the symbolic state is {all_symbols}")
        # set up a SymbolicState instance
        logger.log.info(f"Instantiating new SymbolicState instance with symbols {all_symbols}")
        symbolic_state: SymbolicState = StatementSymbolicState(all_symbols, stmt_ast)
        return symbolic_state
    
    def _process_expression_ast(self, stmt_ast: ast.Expr, stmt_ast_parent_block):
        """
        Instantiate a new SymbolicState instance based on this expression statement.

        TODO: handle more complex ast structures for forming names, for example obj.subobj.var.
        """
        # first, add a reference from stmt_ast to its parent block
        stmt_ast.parent_block = stmt_ast_parent_block
        logger.log.info(f"Instantiating a symbolic state for AST instance stmt_ast = {stmt_ast}")
        # initialise empty list of symbols
        all_symbols: list = []
        # walk the ast to find the symbols used
        for walked_ast in ast.walk(stmt_ast):
            # extract information according to type
            if type(walked_ast) is ast.Name:
                all_symbols.append(walked_ast.id)
        
        # instantiate symbolic state
        logger.log.info(f"Instantiating new SymbolicState instance with symbols {all_symbols}")
        symbolic_state: SymbolicState = StatementSymbolicState(all_symbols, stmt_ast)
        return symbolic_state
    
    def _extract_symbol_names_from_target(self, subast) -> list:
        """
        Given an object from a program ast, extract string representations of the names
        of the symbols used in that ast.
        """
        # initialise an empty list of the symbol names
        symbol_names = []
        # walk the target object to look for ast.Name instances
        for walked_ast in ast.walk(subast):
            if type(walked_ast) is ast.Name:
                symbol_names.append(walked_ast.id)
        return symbol_names
    
    def _extract_function_names(self, subast) -> list:
        """
        Given an object from a program ast, extract string representations of the names
        of the functions used in that ast.
        """
        # initialise an empty list of the function names
        function_names = []
        # walk the ast and extract function names
        for walked_ast in ast.walk(subast):
            if type(walked_ast) is ast.Expr:
                if type(walked_ast.value) is ast.Call:
                    if type(walked_ast.value.func) is ast.Name:
                        function_names.append(walked_ast.value.func.id)
        return function_names