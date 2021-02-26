specification = Specification()\
    .forall(q = changes('a').during('test_package.test3.func1'))\
    .forall(c = future(calls('g').during('test_package.test3.func1')))\
    .check(lambda q, c : (
        one_is_true(
            not_true( q('a') < 1 ),
            q.next(calls('g').during('test_package.test3.func2')).duration() < 1)
        )
    )