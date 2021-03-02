"""
Module containing SCFG factories.
"""

import ast
import os

from VyPR.SCFG.builder import SCFG

def construct_scfg_of_function(module_name: str, module_asts: list, function_name: str) -> SCFG:
    """
    Given a fully-qualified function name, its module and asts of its module,
    find the relevant ast in module_asts and construct the SCFG.

    The format we assume is . for packages, modules and functions, and : for classes.

    For example pkg.module.func, and pkg.module.class:func.
    """
    # initialise the ast of the function we're looking for
    function_ast = None

    # from the module, find the appropriate function ast
    # initialise a list of pairs (path to ast, ast)
    stack = list(map(lambda item : ("", item), module_asts.body))
    while len(stack) > 0:
        top = stack.pop()
        module_path = top[0]
        ast_obj = top[1]
        if type(ast_obj) is ast.FunctionDef:
            # if we have a function definition, check the path
            fully_qualified_function_name = "%s.%s%s" % (module_name, top[0], top[1].name)
            if fully_qualified_function_name == function_name:
                function_ast = ast_obj
        elif hasattr(ast_obj, "body"):
            # if we don't have a function definition, but we have a "body" attribute
            # then we could have a conditional or a class definition
            # (we assume no loops at top-level of a module)
            if type(ast_obj) is ast.If:
                stack += map(
                    lambda item : (module_path, item),
                    ast_obj.body
                )
            elif type(ast_obj) is ast.ClassDef:
                stack += map(
                    lambda item: ("%s%s%s:" %
                                  (module_path, "." if (module_path != "" and module_path[-1] != ":") else "",
                                   ast_obj.name), item),
                    ast_obj.body
                )
    
    # construct the SCFG
    scfg = SCFG(function_ast.body)

    return scfg