"""
Module for command line interface with specification building package.
"""

from VyPR.Specifications.builder import Specification, all_are_true, one_is_true, not_true, timeBetween
from VyPR.Specifications.predicates import changes, calls, future

specification1 = Specification()\
    .forall(q = changes("a").during("func1"))\
    .check(
        lambda q : (
            not_true(
                all_are_true(
                    q('a') < 10,
                    q('a') > 5,
                    q.next(calls('f').during('func2'))
                )
            )
        )
    )

print(specification1)

specification2 = Specification()\
    .forall(c = calls("func").during("func1"))\
    .check(
        lambda c : (
            all_are_true(
                c.duration() < 1,
                c.next(changes('flag').during('func2'))\
                 .next(calls('check').during('func2')).duration() < 1
            )
        )
    )

print(specification2)

specification3 = Specification()\
    .forall(q = changes('a').during('func1'))\
    .forall(c = future(calls('f').during('func2')))\
    .check(
        lambda q, c : (
            timeBetween(q, c.after()) < 4.2
        )
    )

print(specification3)