#!/usr/bin/env python

import random
import timeit

DIC = {}
NB_ITERS = 20000

# ---


def exception():
    for i in xrange(100):
        try:
            a = DIC[i]
        except KeyError:
            a = None

# ---


def test():
    for i in xrange(100):
        if i in DIC:
            a = DIC[i]
        else:
            a = None

# ---


def test2():
    for i in xrange(100):
        a = DIC[i] if i in DIC else None

# ---


def get():
    for i in xrange(100):
        a = DIC.get(i, None)

# ---


def get2():
    getter = DIC.get
    for i in xrange(100):
        a = getter(i, None)

# ---


timers = [timeit.Timer('%s()' % func, 'from __main__ import %s' % func)
          for func in ['exception', 'test', 'test2', 'get', 'get2']]


for rate in [100, 95, 50, 0]:
    DIC = {}
    for i in xrange(100):
        if i < rate:
            DIC[i] = i

    print
    print 'Testing if an element belongs to a dictionary (%d%% success)' % rate
    for i, timer in enumerate(timers, 1):
        print ' * with %d:' % i, timer.timeit(NB_ITERS)
