"""
Module for command line interface with specification building package.
"""

from VyPR.Specifications.builder import Specification
from VyPR.Specifications.predicates import changes, calls

specification = \
    Specification()\
    .forall(q = changes("x"))\
    .check(lambda q : q('x') < 10)

print(specification)