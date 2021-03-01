specification = Specification()\
    .forall(q = changes('a').during('test3.func1'))\
    .check(lambda q : (
        one_is_true(
            not_true( q('a') < 1 ),
            q.next(calls('g').during('test3.func1')).duration() < 1)
        )
    )