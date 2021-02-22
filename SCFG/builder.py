"""
Module containing logic for construction of a symbolic control-flow graph given a Python 3 program.
"""

import ast
import datetime
import graphviz

# temporary solution to logging
h = open(f"logs/scfg/log-{datetime.datetime.now()}", "a")
def log(s):
    global h
    h.write(f"[{datetime.datetime.now()}] {s}\n")

class SymbolicState():

    def __init__(self, symbols_changed: list):
        """
        Store the list of symbols (program variables and functions) whose status
        changed when this symbolic state is reached in the symbolic
        control-flow graph.
        """
        self._symbols_changed: list = symbols_changed
        self._children: list = []
    
    def __repr__(self):
        return f"<SymbolicState (id {id(self)}) _symbols_changed={self._symbols_changed}>"
    
    def add_child(self, child_symbolic_state):
        """
        Add a child symbolic state to self.
        """
        log(f"Add {child_symbolic_state} as child of {self}")
        self._children.append(child_symbolic_state)
    
    def get_children(self) -> list:
        return self._children
    
    def get_symbols_changed(self) -> list:
        return self._symbols_changed


class EmptySymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the root for any symbolic control-flow graph.
    """
    def __init__(self):
        super().__init__([])

class ConditionalEntrySymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for conditionals.
    """
    def __init__(self):
        super().__init__([])

class ConditionalExitSymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for conditionals.
    """
    def __init__(self):
        super().__init__([])

class ForLoopEntrySymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for for-loops.

    The constructor takes the name of the iterator used by the for loop.
    """
    def __init__(self, loop_counter_variables):
        super().__init__(loop_counter_variables)

class ForLoopExitSymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for for-loops.
    """
    def __init__(self):
        super().__init__([])

class WhileLoopEntrySymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for while-loops.
    """
    def __init__(self):
        super().__init__([])

class WhileLoopExitSymbolicState(SymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for while-loops.
    """
    def __init__(self):
        super().__init__([])

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

            log(f"Processing AST {subprogram_ast}")

            # check for the type of the current ast
            if type(subprogram_ast) in [ast.Assign, ast.Expr]:
                log(f"AST {subprogram_ast} is {type(subprogram_ast)} instance")
                # define dictionary from ast types to the processing method to use
                ast_type_to_function = {
                    ast.Assign: self._process_assignment_ast,
                    ast.Expr: self._process_expression_ast
                }
                # instantiate the symbolic state
                new_symbolic_state: SymbolicState = ast_type_to_function[type(subprogram_ast)](subprogram_ast)
                # add it to the list of vertices
                self._symbolic_states.append(new_symbolic_state)
                log(f"Instantiated symbolic state {new_symbolic_state} and added to list of symbolic states for SCFG.")
                # set it as the child of the previous
                log(f"Setting Symbolic State {new_symbolic_state} as child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(new_symbolic_state)
                log(f"Setting previous symbolic state to {new_symbolic_state}")
                previous_symbolic_state = new_symbolic_state

            
            elif type(subprogram_ast) is ast.If:
                log(f"AST {subprogram_ast} is ast.If instance")

                # deal with the main body of the conditional

                # instantiate symbolic states for entry and exit
                log(f"Setting up conditional entry and exit symbolic states")
                entry_symbolic_state: ConditionalEntrySymbolicState = ConditionalEntrySymbolicState()
                exit_symbolic_state: ConditionalExitSymbolicState = ConditionalExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                log(f"Entry state is {entry_symbolic_state} and exit state is {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                log(f"Adding {entry_symbolic_state} as a child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)
                # recursive on the conditional body
                log(f"Recursing on body of conditional, linking to parent {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                log(f"Setting {exit_symbolic_state} as child of block")
                final_body_symbolic_state.add_child(exit_symbolic_state)

                # check for orelse block
                # if there is none, set the conditional exit vertex as a child of the entry vertex
                # if there is, process it as a separate block
                log(f"Checking for existence of orelse block in conditional")
                if len(subprogram_ast.orelse) != 0:
                    log(f"An orelse block was found - recursing with parent {entry_symbolic_state}")
                    # there is an orelse block - process it
                    final_orelse_symbolic_state = self.subprogram_to_scfg(subprogram_ast.orelse, entry_symbolic_state)
                    # link final state with exit state
                    final_orelse_symbolic_state.add_child(exit_symbolic_state)
                else:
                    log(f"No orelse block was found - adding {exit_symbolic_state} as child of {entry_symbolic_state}")
                    # there is no orelse block
                    entry_symbolic_state.add_child(exit_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            elif type(subprogram_ast) is ast.For:
                log(f"AST {subprogram_ast} is ast.For instance")

                # deal with the body of the for loop

                # instantiate symbolic states for entry and exit
                log(f"Setting up for-loop entry and exit symbolic states")
                # derive the list of names of program variables used as loop counters
                loop_counter_variables = self._extract_symbol_names_from_target(subprogram_ast.target)
                log(f"Loop counter variables used by the loop are {loop_counter_variables}")
                # instantiate states
                entry_symbolic_state: ForLoopEntrySymbolicState = ForLoopEntrySymbolicState(loop_counter_variables)
                exit_symbolic_state: ForLoopExitSymbolicState = ForLoopExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                log(f"Entry state is {entry_symbolic_state} and exit state is {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                log(f"Adding {entry_symbolic_state} as a child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)
                # recursive on the loop body
                log(f"Recursing on body of loop, linking to parent {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                log(f"Setting {exit_symbolic_state} as child of block")
                final_body_symbolic_state.add_child(exit_symbolic_state)
                # set for loop entry symbolic state as child of final state in body
                log(f"Setting entry symbolic state {entry_symbolic_state} as child of final state {final_body_symbolic_state}")
                final_body_symbolic_state.add_child(entry_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            elif type(subprogram_ast) is ast.While:
                log(f"AST {subprogram_ast} is ast.While instance")

                # deal with the body of the while loop

                # instantiate symbolic states while entry and exit
                log(f"Setting up while-loop entry and exit symbolic states")
                # instantiate states
                entry_symbolic_state: WhileLoopEntrySymbolicState = WhileLoopEntrySymbolicState()
                exit_symbolic_state: WhileLoopExitSymbolicState = WhileLoopExitSymbolicState()
                self._symbolic_states += [entry_symbolic_state, exit_symbolic_state]
                log(f"Entry state is {entry_symbolic_state} and exit state is {exit_symbolic_state}")
                # set the entry symbolic state as a child of the previous
                log(f"Adding {entry_symbolic_state} as a child of {previous_symbolic_state}")
                previous_symbolic_state.add_child(entry_symbolic_state)
                # recursive on the loop body
                log(f"Recursing on body of loop, linking to parent {entry_symbolic_state}")
                final_body_symbolic_state = self.subprogram_to_scfg(subprogram_ast.body, entry_symbolic_state)
                # set the exit symbolic state as a child of the final one from the body
                log(f"Setting {exit_symbolic_state} as child of block")
                final_body_symbolic_state.add_child(exit_symbolic_state)
                # set for loop entry symbolic state as child of final state in body
                log(f"Setting entry symbolic state {entry_symbolic_state} as child of final state {final_body_symbolic_state}")
                final_body_symbolic_state.add_child(entry_symbolic_state)
                
                # update the previous symbolic state for the next iteration
                previous_symbolic_state = exit_symbolic_state
            
            log(f"Moving to next iteration with previous state {previous_symbolic_state}")
        
        # return the final symbolic state from this subprogram
        return previous_symbolic_state

    
    def write_to_file(self, filename: str):
        """
        Write a dot file of the SCFG.
        """
        log(f"Writing graph file for SCFG.")
        # instantiate directed graph
        graph = graphviz.Digraph()
        graph.attr("graph", splines="true", fontsize="10")
        shape = "rectangle"
        # iterate through symbolic states, draw edges between those that are linked
        # by child/parent
        for symbolic_state in self._symbolic_states:
            log(f"  Processing symbolic state {symbolic_state}")
            if type(symbolic_state) is SymbolicState:
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
        log(f"SCFG written to file {filename}")
    
    def _process_assignment_ast(self, stmt_ast: ast.Assign):
        """
        Instantiate a new SymbolicState instance based on this assignment statement.

        The target program variables, along with any functions called on the right-hand-side
        of the assignment, will be included as symbols changed by that Symbolic State
        """
        log(f"Instantiating symbolic state for AST instance {stmt_ast}")
        # determine the program variables assigned on the left-hand-side
        targets: list = stmt_ast.targets
        # extract names - for now just care about normal program variables, not attributes or functions
        target_names: list = []
        for target in targets:
            target_names += self._extract_symbol_names_from_target(target)
        log(f"List of all program variables changed is {target_names}")
        # extract function names
        assigned_value = stmt_ast.value
        function_names: list = self._extract_function_names(assigned_value)
        log(f"List of all program functions called is {function_names}")
        # merge the two lists of symbols
        all_symbols: list = target_names + function_names
        log(f"List of all symbols to mark as changed in the symbolic state is {all_symbols}")
        # set up a SymbolicState instance
        log(f"Instantiating new SymbolicState instance with symbols {all_symbols}")
        symbolic_state: SymbolicState = SymbolicState(all_symbols)
        return symbolic_state
    
    def _process_expression_ast(self, stmt_ast: ast.Expr):
        """
        Instantiate a new SymbolicState instance based on this expression statement.

        TODO: handle more complex ast structures for forming names, for example obj.subobj.var.
        """
        log(f"Instantiating a symbolic state for AST instance {stmt_ast}")
        # initialise empty list of symbols
        all_symbols: list = []
        # walk the ast to find the symbols used
        for walked_ast in ast.walk(stmt_ast):
            # extract information according to type
            if type(walked_ast) is ast.Name:
                all_symbols.append(walked_ast.id)
        
        # instantiate symbolic state
        log(f"Instantiating new SymbolicState instance with symbols {all_symbols}")
        symbolic_state: SymbolicState = SymbolicState(all_symbols)
        return symbolic_state
    
    def _extract_symbol_names_from_target(self, subast) -> list:
        """
        Given an object from a program ast, extract string representations of the names
        of the symbols used in that ast.
        """
        # initialise an empty list of the symbol names
        symbol_names = []
        # check the type of the ast
        if type(subast) is ast.Name:
            symbol_names.append(subast.id)
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