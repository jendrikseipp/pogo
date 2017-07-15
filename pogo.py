#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys

# The following line is adapted automatically by "make install".
prefix = '/usr'

installed_dir = os.path.join(prefix, 'share/pogo/')
local_dir = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(local_dir, 'pogo')):
    print('Running local pogo version.')
    app_dir = local_dir
elif os.path.exists(installed_dir):
    print('Running installed pogo version.')
    app_dir = installed_dir
else:
    sys.exit('Source files could not be found')

sys.path.insert(0, app_dir)

from pogo import __main__
__main__.main()
