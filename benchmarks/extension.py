#!/usr/bin/env python

import os
import re
import timeit

from os.path import splitext

LIST = [
    'truc.Mp3', 'foo', 'foo.OGG', 'Bidule.tXt', 'bar.vim', 'test.wav',
    'hello.mp3', 'yeah.flac', 'dfsfdsa', 'dass.MPC', 'dfdsaaads.fsad']
NB_ITERS = 200000

# ---

mFormatsRE = re.compile(r'^.*\.(mp3|ogg|mpc|flac)$', re.IGNORECASE)


def re():
    for word in LIST:
        if mFormatsRE.match(word):
            pass

# ---


def ew():
    for word in LIST:
        w2 = word.lower()
        if w2.endswith('.mp3') or w2.endswith('.ogg') or w2.endswith('.mpc') or w2.endswith('.flac'):
            pass

# ---


def ew_lc():
    for word in [w.lower() for w in LIST]:
        if word.endswith('.mp3') or word.endswith('.ogg') or word.endswith('.mpc') or word.endswith('.flac'):
            pass

# ---


exts = set(['.mp3', '.ogg', '.mpc', '.flac'])


def ss_set():
    for word in LIST:
        w2 = word.lower()
        if w2[-4:] in exts or w2[-5:] in exts:
            pass

# ---


exts2 = {'.mp3': None, '.ogg': None, '.mpc': None, '.flac': None}


def ss_dic():
    for word in LIST:
        w2 = word.lower()
        if w2[-4:] in exts2 or w2[-5:] in exts2:
            pass

# ---


def ss_dic_split():
    for word in LIST:
        if splitext(word)[1].lower() in exts2:
            pass


print 'Testing what is the extension of a given file'

t1 = timeit.Timer('re()', 'from __main__ import re')
t2 = timeit.Timer('ew()', 'from __main__ import ew')
t3 = timeit.Timer('ew_lc()', 'from __main__ import ew_lc')
t4 = timeit.Timer('ss_set()', 'from __main__ import ss_set')
t5 = timeit.Timer('ss_dic()', 'from __main__ import ss_dic')
t6 = timeit.Timer('ss_dic_split()', 'from __main__ import ss_dic_split')

print ' * regular expression:', t1.timeit(NB_ITERS)
print ' * endswith() 1:      ', t2.timeit(NB_ITERS)
print ' * endswith() 2:      ', t3.timeit(NB_ITERS)
print ' * substring + set:   ', t4.timeit(NB_ITERS)
print ' * substring + dic:   ', t5.timeit(NB_ITERS)
print ' * splitext() + dic:  ', t6.timeit(NB_ITERS)
