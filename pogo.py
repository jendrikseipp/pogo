#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys

# The following line is adapted automatically by "make install".
prefix = '/usr'

local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pogo')
global_dir = os.path.join(prefix, 'share', 'pogo', 'pogo')


def get_app_dir():
    print('Checking local path {}'.format(local_dir))
    if os.path.isdir(local_dir):
        return local_dir

    print('Checking global path {}'.format(global_dir))
    if os.path.isdir(global_dir):
        return global_dir

    sys.exit('Pogo source files could not be found. Aborting.')


app_dir = get_app_dir()
print('Using pogo version at {}'.format(app_dir))
sys.path.insert(0, os.path.dirname(app_dir))

from pogo import __main__
__main__.main()
