#!/usr/bin/env python

import os

TEMP_FILE = '/tmp/foo'

print 'All .po files will be scanned to remove translations of "gtk-*" messages.\n'


for file in ['./' + f for f in os.listdir('./') if f.endswith('.po')]:
    print ' * Fixing %s' % (os.path.basename(file))

    input   = open(file,      'r')
    output  = open(TEMP_FILE, 'w')
    delNext = False

    for line in input:
        if line.startswith('msgid "gtk-'): delNext = True
        elif delNext:                      delNext = False
        else:                              output.write(line)

    input.close()
    output.close()
    os.system('mv %s %s' % (TEMP_FILE, file))
