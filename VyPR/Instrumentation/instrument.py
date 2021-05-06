"""
Module containing the logic for adding instrumentation code based on the results of static analysis with respect to iCFTL specifications.
"""

import os
import ast
from shutil import copyfile

from VyPR.Instrumentation.analyse import Analyser
from VyPR.Instrumentation.prepare import prepare_specification
from VyPR.Specifications.constraints import (ValueInConcreteState,
                                                ValueLengthInConcreteState,
                                                DurationOfTransition,
                                                ConcreteStateBeforeTransition,
                                                ConcreteStateAfterTransition,
                                                TimeBetween)
from VyPR.SCFG.prepare import construct_scfg_of_function
import VyPR.Logging.logger as logger

class Instrument():
    """
    Class used to invoke Analyser in order to perform static analysis,
    modify the ASTs of files to be instrumented and perform the final compilation.
    """

    def __init__(self, specification_file: str, root_directory: str, assume_flask: bool):
        """
        Invoke analyser with the specification file and root directory given.
        """
        # store the root directory
        self._root_directory = root_directory

        # remember whether or not to assume Flask in the instrumentation code we place
        self._assume_flask = assume_flask

        logger.log.info("Importing specification to set self._specification")

        # import specification from the file given
        self._specification = prepare_specification(specification_file)

        logger.log.info(f"Imported specification is\n{self._specification}")

        # get a list of all functions used in the specification
        logger.log.info("Calling self._specification.get_function_names_used to get a list of all modules relevant to the specification")
        self._all_functions = self._specification.get_function_names_used()
        # get the list of all modules that contain functions referred to in the specification
        logger.log.info("Calling self._derive_list_of_modules to get a list of all modules relevant to the specification")
        self._all_modules = self._derive_list_of_modules()

        # reset instrumented files
        logger.log.info("Removing existing instrumented files")
        self._reset_instrumented_files()

        # get the ASTs and lines of each of these modules
        logger.log.info("Getting AST and source code line list for each module")
        self._module_to_ast_list = {}
        self._module_to_lines = {}
        # iterate through modules and construct ASTs for each
        for module in self._all_modules:
            # get asts
            self._module_to_ast_list[module] = self._get_asts_from_module(module)
            # get code lines
            self._module_to_lines[module] = self._get_lines_from_module(module)

        # get the scfg of each of these functions
        logger.log.info("Constructing SCFGs of each function")
        # initialise empty map
        self._function_name_to_scfg_map = {}
        # get SCFG and AST for each function
        for function in self._all_functions:
            logger.log.info(f"Calling construct_scfg_of_function on function '{function}'")
            # get module from function
            module = self._get_module_from_function(function)
            # get scfg for this function based on self._filename_to_ast_list[filename]
            self._function_name_to_scfg_map[function] = \
                construct_scfg_of_function(module, self._module_to_ast_list[module], function)
            # write to file
            self._function_name_to_scfg_map[function].write_to_file(f"{function}.gv")
        
        # initialise the analyser class
        logger.log.info("Instantiating Analyser")
        self._analyser = Analyser(self._specification, self._function_name_to_scfg_map)

        # compute the instrumentation tree and the list of elements to instrument based on quantifiers
        logger.log.info("Determining statements in modules that must be instrumented")
        self._quantifier_instrumentation_points, self._instrumentation_tree = \
            self._analyser.compute_instrumentation_points()
    
    def _derive_list_of_modules(self):
        """
        Derive the list of modules from self._all_functions.

        For now, just split by ., remove the last element of the list, and join back together.
        """
        # initialise empty list of modules
        all_modules = []
        # iterate through functions, getting the module name
        for function in self._all_functions:
            # split the function name
            sequence = function.split(".")
            # remove the function part
            module_part = sequence[:-1]
            # join to get the module name
            module_name = ".".join(module_part)
            # add to list
            if module_name not in all_modules:
                all_modules.append(module_name)
        
        return all_modules
    
    def _reset_instrumented_files(self):
        """
        For each module in self._all_modules, if the backup generated by VyPR exists,
        rename it to the original filename.
        """
        # iterate through modules
        for module in self._all_modules:
            # get backup and original filenames
            backup_filename = self._get_backup_filename_from_module(module)
            original_filename = self._get_original_filename_from_module(module)
            # check for existence
            if os.path.isfile(backup_filename):
                # rename
                os.rename(backup_filename, original_filename)
    
    def _get_module_from_function(self, function: str) -> str:
        """
        Given a function name, extract the module.
        """
        # split the function name
        sequence = function.split(".")
        # remove the function part
        module_part = sequence[:-1]
        # join to get the module name
        module_name = ".".join(module_part)
        return module_name
    
    def _get_asts_from_module(self, module: str) -> list:
        """
        Given a module, get its filename, read in the code from it and construct the ASTs.
        """
        # translate module to have / instead of .
        module = module.replace(".", "/")
        # get filename
        filename = os.path.join(self._root_directory, f"{module}.py")
        # construct file handle
        with open(filename, "r") as h:
            code = h.read()
            asts = ast.parse(code)
            
        return asts
    
    def _get_lines_from_module(self, module: str) -> list:
        """
        Given a module, gets its filename and read in the code lines from it.
        """
        # translate module to have / instead of .
        module = module.replace(".", "/")
        # get filename
        filename = os.path.join(self._root_directory, f"{module}.py")
        # construct file handle
        with open(filename, "r") as h:
            # get trippes lines
            lines = list(map(lambda line : line.rstrip(), h.readlines()))
        
        return lines
    
    def insert_instruments(self):
        """
        Traverse the instrumentation tree structure and, for each symbolic state,
        place an instrument at an appropriate position around the AST provided by the symbolic state.
        """
        logger.log.info("Inserting instruments into source code")
        # get atomic constraints of the specification so we can decide on what each instrument should look like
        atomic_constraints = self._specification.get_constraint().get_atomic_constraints()
        logger.log.info(f"atomic_constraints = {atomic_constraints}")
        # initialise empty list of triples (module_name, line_index, instrument_code)
        list_of_instrument_triples = []
        # traverse self._instrumentation_tree in order to insert instrumentation points for quantifiers
        logger.log.info("Inserting instruments for constraints")
        for (map_index, current_map) in enumerate(self._quantifier_instrumentation_points):
            logger.log.info(f"map_index = {map_index}")
            # iterate through the variables of the map
            for variable in current_map:
                # get the symbolic state
                symbolic_state = current_map[variable]
                # get the index in the block of asts where the instrument's code will be inserted
                index_in_block = symbolic_state.get_ast_object().parent_block.index(symbolic_state.get_ast_object())
                # get the line number at which to insert the code
                line_number = symbolic_state.get_ast_object().parent_block[index_in_block].lineno
                # get the index in the list of lines
                line_index = line_number - 1
                # get the function inside which symbolic_state is found
                function = self._analyser.get_scfg_searcher().get_function_name_of_symbolic_state(symbolic_state)
                # derive the module name from the function
                module = self._get_module_from_function(function)
                # generate the code
                quantifier_instrument_code = self._generate_quantifier_instrument_code(
                    module,
                    line_index,
                    map_index,
                    variable
                )
                # append
                list_of_instrument_triples.append((module, line_index, quantifier_instrument_code))
                    
        # traverse self._instrumentation_tree in order to insert instrumentation points for constraints
        logger.log.info("Inserting instruments for constraints")
        for map_index in self._instrumentation_tree:
            logger.log.info(f"map_index = {map_index}")
            for atom_index in self._instrumentation_tree[map_index]:
                logger.log.info(f"atom_index = {atom_index}")
                # get the atom at atom_index
                relevant_atom = atomic_constraints[atom_index]
                logger.log.info(f"relevant_atom = {relevant_atom}")
                # iterate through the subatom indices
                for subatom_index in self._instrumentation_tree[map_index][atom_index]:
                    logger.log.info(f"subatom_index = {subatom_index}")
                    # get the subatom at subatom_index
                    relevant_subatom = relevant_atom.get_expression(subatom_index)
                    logger.log.info(f"relevant_subatom = {relevant_subatom}")
                    # iterate through the symbolic states
                    for symbolic_state in self._instrumentation_tree[map_index][atom_index][subatom_index]:
                        logger.log.info(f"Processing symbolic_state = {symbolic_state}")
                        # get the index in the block of asts where the instrument's code will be inserted
                        index_in_block = symbolic_state.get_ast_object().parent_block.index(symbolic_state.get_ast_object())
                        # get the line number at which to insert the code
                        line_number = symbolic_state.get_ast_object().parent_block[index_in_block].lineno
                        # get the index in the list of lines
                        line_index = line_number - 1
                        # get the function inside which symbolic_state is found
                        function = self._analyser.get_scfg_searcher().get_function_name_of_symbolic_state(symbolic_state)
                        # derive the module name from the function
                        module = self._get_module_from_function(function)
                        logger.log.info(f"Generating list of instrument triples with "\
                            f"index_in_block={index_in_block}, line_number={line_number}, line_index={line_index}, function={function}, module={module}")
                        # generate and append the instrument code
                        list_of_instrument_triples += self._generate_constraint_instrument_code(
                            module,
                            line_index,
                            map_index,
                            atom_index,
                            subatom_index,
                            relevant_subatom
                        )
        
        # sort instrument code by line index descending (that way we don't have to recompute line numbers)
        # we rely on this sorting being stable - otherwise some variables defined by instruments could be undefined
        # if they're used before their definition
        # get list of instrument triples
        list_of_instrument_triples = list(reversed(sorted(list_of_instrument_triples, key=lambda triple : triple[1])))
        # insert the instruments
        for triple in list_of_instrument_triples:
            # get the module inside which this instrument should be placed
            module_name = triple[0]
            # insert instrument
            self._module_to_lines[module_name].insert(triple[1], triple[2])
        
        # now, insert additional imports
        imports = """import datetime as vypr_dt"""
        lines = imports.split("\n")
        # for each module, insert these lines at the beginning
        for module_name in self._module_to_lines:
            # insert lines (reversed, since each time we insert at the beginning)
            for line in reversed(lines):
                self._module_to_lines[module_name].insert(0, line)
    
    def get_indentation_level_of_stmt(self, stmt: str) -> int:
        """
        Given a statement, assuming indentation is performed using spaces, count the number of spaces.
        """
        # initialise number of spaces
        number_of_spaces = 0
        # iterate through the string until a non-space character is found
        for i in range(len(stmt)):
            if stmt[i] != " ":
                break
            else:
                number_of_spaces += 1
        
        return number_of_spaces
    
    def _generate_quantifier_instrument_code(self, module_name: str, line_index: int, map_index: int, variable: str):
        """
        Given all necessary information, generate the instrumentation code for a quantifier.
        """
        logger.log.info(f"Getting lines of module_name = {module_name}")
        # get the module lines
        module_lines = self._module_to_lines[module_name]
        # get the indentation level of the code to be inserted
        indentation_level = self.get_indentation_level_of_stmt(module_lines[line_index])
        # generate instrument code
        # TODO: make function the instrument calls a parameter
        # construct the indentation string
        indentation = " "*indentation_level
        # define instrument function
        base = "g.vypr" if self._assume_flask else "vypr"
        instrument_function = f"{base}.send_trigger"
        # check the instrument type
        logger.log.info(f"Generating instrument code for quantifier with variable = {variable}, based on map_index = {map_index}")
        code = f"""{indentation}{instrument_function}({map_index}, '{variable}')"""
        return code
    
    def _generate_constraint_instrument_code(self, module_name: str, line_index: int, map_index: int, atom_index: int, subatom_index: int, subatom):
        """
        Given all of the necessary information, generate the instrumentation code for a constraint.
        """
        logger.log.info(f"Getting lines of module_name = {module_name}")
        # get the module lines
        module_lines = self._module_to_lines[module_name]
        # get the indentation level of the code to be inserted
        indentation_level = self.get_indentation_level_of_stmt(module_lines[line_index])
        # generate instrument code
        # TODO: make function the instrument calls a parameter
        # construct the indentation string
        indentation = " "*indentation_level
        # define instrument function
        base = "g.vypr" if self._assume_flask else "vypr"
        instrument_function = f"{base}.send_measurement"
        # check the instrument type
        logger.log.info(f"Generating measurement instrument code according to subatom = {subatom} with type {type(subatom)}")
        if type(subatom) is ValueInConcreteState:
            # construct the instrument code
            code = f"""{indentation}{instrument_function}({map_index}, {atom_index}, {subatom_index}, {subatom.get_program_variable()})"""
            code = [(module_name, line_index+1, code)]
        elif type(subatom) is ValueLengthInConcreteState:
            # construct the instrument code
            code = f"""{indentation}{instrument_function}({map_index}, {atom_index}, {subatom_index}, len({subatom.get_value_expression().get_program_variable()}))"""
            code = [(module_name, line_index+1, code)]
        elif type(subatom) is DurationOfTransition:
            # construct measurement code
            measurement_start_code = "ts_start = vypr_dt.datetime.now()"
            measurement_end_code = "ts_end = vypr_dt.datetime.now()"
            measurement_difference_code = "duration = (ts_end - ts_start).total_seconds()"
            # construct the instrument code
            code_part_1 = \
                f"""{indentation}{measurement_start_code}"""
            code_part_2 = \
                f"""{indentation}{measurement_end_code}"""
            code_part_3 = \
                f"""{indentation}{measurement_difference_code}; {instrument_function}({map_index}, {atom_index}, {subatom_index}, duration)"""
            code = [(module_name, line_index, code_part_1), (module_name, line_index+1, code_part_2), (module_name, line_index+1, code_part_3)]
        elif type(subatom) is ConcreteStateBeforeTransition:
            # construct measurement code
            measurement_code = f"ts_{subatom_index} = vypr_dt.datetime.now()"
            # construct the instrument code
            instrument_code = f"""{indentation}{measurement_code}; {instrument_function}({map_index}, {atom_index}, {subatom_index}, ts_{subatom_index})"""
            code = [(module_name, line_index, instrument_code)]
        elif type(subatom) is ConcreteStateAfterTransition:
            # construct measurement code
            measurement_code = f"ts_{subatom_index} = vypr_dt.datetime.now()"
            # construct the instrument code
            instrument_code = f"""{indentation}{measurement_code}; {instrument_function}({map_index}, {atom_index}, {subatom_index}, ts_{subatom_index})"""
            code = [(module_name, line_index+1, instrument_code)]
        
        return code
    
    def _get_original_filename_from_module(self, module: str) -> str:
        """
        Given a module name, derive its filename.
        """
        # begin to convert to filename
        with_slashes = module.replace(".", "/").replace(".py", "")
        # join with root directory
        filename = os.path.join(self._root_directory, f"{with_slashes}.py")
        return filename
    
    def _get_backup_filename_from_module(self, module: str) -> str:
        """
        Given a module name, derive its filename.
        """
        # begin to convert to filename
        with_slashes = module.replace(".", "/").replace(".py", "")
        # join with root directory
        filename = os.path.join(self._root_directory, f"{with_slashes}_vypr_original.py")
        return filename
    
    def compile(self):
        """
        Given the modified source code of the modules, write new files (backup old files).
        """
        logger.log.info("Writing instrumented code")
        # iterate through modules
        for module in self._all_modules:
            logger.log.info(f"Processing module = {module}")

            # get lines for this module
            lines = self._module_to_lines[module]
            # add new lines
            lines = list(map(lambda line : f"{line}\n", lines))

            # get the original and backup filenames from the module
            original_filename = self._get_original_filename_from_module(module)
            backup_filename = self._get_backup_filename_from_module(module)

            logger.log.info(f"Instrumenting original_filename = {original_filename}, while keeping a backup in backup_filename = {backup_filename}")

            # if it exists, rename the backup to the original
            if os.path.isfile(backup_filename):
                os.rename(backup_filename, original_filename)
            
            # copy the original to a backup
            copyfile(original_filename, backup_filename)

            # write the lines for the module to the source file
            with open(original_filename, "w") as h:
                h.writelines(lines)