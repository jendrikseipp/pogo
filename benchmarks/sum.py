#!/usr/bin/env python

import timeit

LIST = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [12, 14], [15, 16], [17, 18], [19, 20]]
NB_ITERS = 500000

# ---


def withLoop():
    s = 0
    for value in LIST:
        s += value[1]
    return s

# ---


def withSum():
    return sum([value[1] for value in LIST])

# ---


t1 = timeit.Timer('withLoop()', 'from __main__ import withLoop')
t2 = timeit.Timer('withSum()', 'from __main__ import withSum')


print
print 'Summing some elements in a list'
print ' * with a loop              :', t1.timeit(NB_ITERS)
print ' * with a list comprehension:', t2.timeit(NB_ITERS)
