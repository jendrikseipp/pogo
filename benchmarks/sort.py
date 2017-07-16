#!/usr/bin/env python

import timeit

LIST = [
    834, 29, 99, 473, 128, 43, 555, 3243, 666, 12, 0, 3223, 5533, 3214,
    987, 4325, 87, 324, 45324, 980, 2343, 92, 23, 45, 433]
NB_ITERS = 500000

# ---


def withSort():
    mylist = [item for item in LIST]
    mylist.sort()
    return mylist


# ---

def withSorted():
    mylist = [item for item in LIST]
    return sorted(mylist)

# ---


t1 = timeit.Timer('withSort()', 'from __main__ import withSort')
t2 = timeit.Timer('withSorted()', 'from __main__ import withSorted')

print
print 'Sorting a list'
print ' * with an inplace sort() :', t1.timeit(NB_ITERS)
print ' * with a call to sorted():', t2.timeit(NB_ITERS)
