specification = Specification()\
    .forall(q = changes('a').during('test4.func1'))\
    .forall(t = future(calls('g').during('test4.func1')))\
    .check(
        lambda q, t : (
            all_are_true(
                q('a') < 20,
                t.duration() < 1
            )
        )
    )