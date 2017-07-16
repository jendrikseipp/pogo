#!/usr/bin/env python

import timeit

from hsaudiotag import auto


FILE = '/home/jendrik/You Cannot Cast Out The Demons (You Might As Well Dance).mp3'
NB_ITERS = 5000


class File(object):
    """Automatically determine a file type and decode it accordingly, providing a unified interface
    to all file types.
    """

    def __init__(self, infile):
        self.valid = False
        f = auto.File._guess_class(infile)
        self.original = f
        self.tag = f.tag if hasattr(f, 'tag') else f
        if f is not None:
            self.valid = True
            if hasattr(f, 'close'):
                f.close()

    def __getattr__(self, name):
        if name in auto.AUDIO_ATTRS:
            return getattr(self.original, name, None)
        return getattr(self.tag, name, None)


def auto_default():
    myfile = auto.File(FILE)
    report(myfile)


def auto_lazy():
    myfile = File(FILE)
    report(myfile)


def report(audiofile):
    audiofile.artist
    audiofile.album
    audiofile.title
    audiofile.track
    audiofile.duration


timers = ['auto_default', 'auto_lazy']

for name in timers:
    timer = timeit.Timer('%s()' % name, 'from __main__ import %s' % name)
    print '%15s:' % name, timer.timeit(NB_ITERS)
