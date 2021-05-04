"""
Module to contain definitions of various kinds of symbolic states.
"""

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

class TryEntrySymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the entry symbolic state for try-excepts.
    """
    def __init__(self, ast_obj):
        super().__init__()
        self._ast_obj = ast_obj

class TryExitSymbolicState(ControlFlowSymbolicState):
    """
    A symbolic state class to be used as the exit symbolic state for try-excepts.
    """
    def __init__(self):
        super().__init__()