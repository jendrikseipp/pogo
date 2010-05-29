#!/usr/bin/env python

import os

for gladeFile in [os.path.join('./', file) for file in os.listdir('./') if file.endswith('.glade')]:
    os.system('vim %s -c "%%g/^<!--.*-->$/d" -c "%%g/^.*GDK_POINTER_MOTION_MASK.*$/d" -c "%%s/^\\s\\+//" -c "x"' % gladeFile)
