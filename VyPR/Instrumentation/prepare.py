"""
Module containing logic for preparation for instrumentation.
"""

def prepare_specification(filename: str):
    """
    Given the filename in which the specification is found,
    read it in, add necessary imports, then write to a temporary file
    ready for import.
    """
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
    with open("tmp_spec.py", "w") as h:
        h.write(specification_code)

    # import the specification
    from tmp_spec import specification

    return specification