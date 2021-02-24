"""
Module for command line interface with specification building package.
"""

from VyPR.Specifications.builder import Specification, all_are_true, one_is_true, not_true
from VyPR.Specifications.predicates import changes, calls

specification1 = Specification()\
    .forall(q = changes("a").during("func1"))\
    .check(
        lambda q : (
            not_true(
                one_is_true(
                    not_true(
                        all_are_true(
                            q('a') < 10,
                            q('a') > 5
                        )
                    ),
                    q('a') < 1
                )
            )
        )
    )

print(specification1)

specification2 = Specification()\
    .forall(c = calls("func").during("func1"))\
    .check(lambda c : c.duration() < 1)

print(specification2)