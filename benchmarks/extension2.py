#!/usr/bin/env python

import os
import re
import timeit

from os.path import splitext

LIST = [
    'truc.Mp3', 'foo', 'foo.OGG', 'Bidule.tXt', 'bar.vim', 'test.wav',
    'hello.mp3', 'yeah.flac', 'dfsfdsa', 'dass.MPC', 'dfdsaaads.fsad']
NB_ITERS = 200000

formats = {'.mp3': None, '.ogg': None, '.mpc': None, '.flac': None}

# ---


def ss():
    for word in LIST:
        w2 = word.lower()
        try:
            m = formats[w2[-4:]]
        except:
            try:
                m = formats[w2[-5:]]
            except:
                m = None

# ---


def sp():
    for word in LIST:
        try:
            m = formats[splitext(word)[1].lower()]
        except:
            m = None

# ---


print 'Retrieving the right module based on the extension'

t1 = timeit.Timer('ss()', 'from __main__ import ss')
t2 = timeit.Timer('sp()', 'from __main__ import sp')

print ' * substring: ', t1.timeit(NB_ITERS)
print ' * splitext:  ', t2.timeit(NB_ITERS)
