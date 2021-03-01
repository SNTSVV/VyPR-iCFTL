"""
Module containing SCFG factories.
"""

import ast
import os

from VyPR.SCFG.builder import SCFG

def construct_scfg_of_function(root_directory: str, function_name: str) -> SCFG:
    """
    Given a fully-qualified function name, find the relevant ast in a source file and construct the SCFG.

    The format we assume is . for packages, modules and functions, and : for classes.

    For example pkg.module.func, and pkg.module.class:func.
    """
    # split the function name into tokens based on .
    # we will import the module based on this, and then use the rest of the
    # string to find the relevant function

    # initialise empty list of tokens
    tokens = []
    # initialise a variable for the last index at which we split up
    # the string
    previous_index = 0
    # iterate through the indices in the function_name string
    for index in range(len(function_name)):
        # if we've seen ., split the string
        if function_name[index] in ".":
            # add a pair of the relevant substring as a token
            tokens.append(function_name[previous_index:index])
            # set the previous index as the next index
            previous_index = index+1
    
    # determine the module name with dot syntax
    module_name = ".".join(tokens)

    # determine the module file name
    module_filename = f"{'/'.join(tokens)}.py"
    module_filename = os.path.join(root_directory, module_filename)

    # determine the function path (by taking the rest of the module name)
    function_path = function_name[len(module_name)+1:]

    # get the ast of the module
    with open(module_filename, "r") as h:
        module_code = h.read()
        module_ast = ast.parse(module_code)
    
    # initialise the ast of the function we're looking for
    function_ast = None

    # from the module, find the appropriate function ast
    # initialise a list of pairs (path to ast, ast)
    stack = list(map(lambda item : ("", item), module_ast.body))
    while len(stack) > 0:
        top = stack.pop()
        module_path = top[0]
        ast_obj = top[1]
        if type(ast_obj) is ast.FunctionDef:
            # if we have a function definition, check the path
            fully_qualified_function_name = "%s%s" % (top[0], top[1].name)
            if fully_qualified_function_name == function_path:
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

    return function_ast.body, scfg