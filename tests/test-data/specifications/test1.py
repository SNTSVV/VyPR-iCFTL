specification = Specification()\
    .forall(q = changes('a').during('test3.func1'))\
    .check(
        lambda q : (
            all_are_true(
                q('a') < 20,
                q.next(calls('g').during('test3.func2')).duration() < 1
            )
        )
    )