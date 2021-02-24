"""
Module for command line interface with specification building package.
"""

from VyPR.Specifications.builder import Specification
from VyPR.Specifications.predicates import changes, calls

specification = \
    Specification()\
    .forall(q = changes("a").during("func1"))\
    .check(lambda q : q('a') < 10)

print(specification)