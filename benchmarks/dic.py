#!/usr/bin/env python

import random, timeit

DIC      = {}
NB_ITERS = 20000

# ---

def exception():
    for i in xrange(100):
        try:    a = DIC[i]
        except: a = None

# ---

def test():
    for i in xrange(100):
        if i in DIC: a = DIC[i]
        else:        a = None

# ---

t1 = timeit.Timer('exception()', 'from __main__ import exception')
t2 = timeit.Timer('test()', 'from __main__ import test')

DIC = {}
for i in xrange(100):
    if i < 100:
        DIC[i] = i

print
print 'Testing if an element belongs to a dictionnary (100% success)'
print ' * with an exception:', t1.timeit(NB_ITERS)
print ' * with a test:      ', t2.timeit(NB_ITERS)

DIC = {}
for i in xrange(100):
    if i < 95:
        DIC[i] = i

print
print 'Testing if an element belongs to a dictionnary (95% success)'
print ' * with an exception:', t1.timeit(NB_ITERS)
print ' * with a test:      ', t2.timeit(NB_ITERS)

DIC = {}
for i in xrange(100):
    if i < 50:
        DIC[i] = i

print
print 'Testing if an element belongs to a dictionnary (50% success)'
print ' * with an exception:', t1.timeit(NB_ITERS)
print ' * with a test:      ', t2.timeit(NB_ITERS)

DIC = {}
for i in xrange(100):
    if i < 0:
        DIC[i] = i

print
print 'Testing if an element belongs to a dictionnary (0% success)'
print ' * with an exception:', t1.timeit(NB_ITERS)
print ' * with a test:      ', t2.timeit(NB_ITERS)
