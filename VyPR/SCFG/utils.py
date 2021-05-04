"""
Module to provide utility functions for SCFG construction.
"""
import ast

import VyPR.Logging.logger as logger

from VyPR.SCFG.symbolic_states import SymbolicState, StatementSymbolicState

def process_assignment_ast(stmt_ast: ast.Assign, stmt_ast_parent_block):
        """
        Instantiate a new SymbolicState instance based on this assignment statement.

        The target program variables, along with any functions called on the right-hand-side
        of the assignment, will be included as symbols changed by that Symbolic State
        """
        logger.log.info("Generating SymbolicState instance from assignment ast")
        # first, add a reference from stmt_ast to its parent block
        stmt_ast.parent_block = stmt_ast_parent_block
        logger.log.info("Instantiating symbolic state for AST instance stmt_ast = %s" % stmt_ast)
        # determine the program variables assigned on the left-hand-side
        targets: list = stmt_ast.targets
        # extract names - for now just care about normal program variables, not attributes or functions
        logger.log.info("Extracting list of assignment target names")
        target_names: list = []
        for target in targets:
            target_names += extract_symbol_names_from_target(target)
        logger.log.info("List of all program variables changed is %s" % target_names)
        # extract function names
        assigned_value = stmt_ast.value
        function_names: list = extract_function_names(assigned_value)
        logger.log.info("List of all program functions called is %s" % function_names)
        # merge the two lists of symbols
        logger.log.info("Merging lists of assignment target names and function names")
        all_symbols: list = target_names + function_names
        logger.log.info("List of all symbols to mark as changed in the symbolic state is %s" % all_symbols)
        # set up a SymbolicState instance
        logger.log.info("Instantiating new StatementSymbolicState instance with all_symbols = %s" % all_symbols)
        symbolic_state: SymbolicState = StatementSymbolicState(all_symbols, stmt_ast)
        return symbolic_state
    
def process_expression_ast(stmt_ast: ast.Expr, stmt_ast_parent_block):
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
    logger.log.info(f"Instantiating new StatementSymbolicState instance with symbols {all_symbols}")
    symbolic_state: SymbolicState = StatementSymbolicState(all_symbols, stmt_ast)
    return symbolic_state

def extract_symbol_names_from_target(subast) -> list:
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

def extract_function_names(subast) -> list:
    """
    Given an object from a program ast, extract string representations of the names
    of the functions used in that ast.
    """
    # initialise an empty list of the function names
    function_names = []
    # walk the ast and extract function names
    for walked_ast in ast.walk(subast):
        if type(walked_ast) is ast.Call:
            if type(walked_ast.func) is ast.Name:
                function_names.append(walked_ast.func.id)
    return function_names