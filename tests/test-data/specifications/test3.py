specification = Specification()\
    .forall(c = calls('f').during('test1.func1'))\
    .check(lambda c : c.duration() < 1)