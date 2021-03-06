"""

Copyright (C) 2021 University of Luxembourg
Developed by Dr. Joshua Heneage Dawes.

Module containing logic for preparation for instrumentation.
"""

import logging
logger = logging.getLogger("VyPR")

def prepare_specification(filename: str):
    """
    Given the filename in which the specification is found,
    read it in, add necessary imports, then write to a temporary file
    ready for import.
    """
    logger.info(f"Reading specification from file '{filename}'")
    # read specification, add imports, write to temporary specification file
    with open(filename, "r") as h:
        # read
        specification_code = h.read()
        # add imports
        specification_code = f"""
from VyPR.Specifications.builder import Specification, all_are_true, one_is_true, not_true, timeBetween
from VyPR.Specifications.predicates import changes, calls, future

{specification_code}
        """

    # write to temporary file
    logger.info("Writing full specification code to temporary file 'tmp_spec.py'")
    with open("tmp_spec.py", "w") as h:
        h.write(specification_code)

    # import the specification
    logger.info("Importing specification from newly written module")
    from tmp_spec import specification

    return specification