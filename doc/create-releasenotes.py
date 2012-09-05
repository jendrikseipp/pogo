#! /usr/bin/env python

import os
import sys

# Change into this file's directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

NEWS = 'NEWS'
NOTES = '../RELEASENOTES'

lines = []

lineno = 0
with open(NEWS) as news:
    for line in news:
        lineno += 1

        # Exclude everything after we find an empty line.
        if lineno > 4 and not line.strip():
            break
        # Include everything from line 4.
        elif lineno >= 4:
            lines.append(line)

with open(NOTES, 'w') as notes:
    notes.writelines(lines)
