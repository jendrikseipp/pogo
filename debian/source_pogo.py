'''apport package hook for pogo.

Code adapted from the novacut project.

(c) 2012 Novacut Inc
Author: Jason Gerard DeRose <jderose@novacut.com>
'''

import os
from os import path

from apport.hookutils import attach_file_if_exists

LOGS = (
    ('DebugLog', 'log'),
)

def add_info(report):
    report['CrashDB'] = 'pogo'
    pogo_dir = path.join(os.environ['HOME'], '.config', 'pogo', 'Logs')
    for (key, name) in LOGS:
        log = path.join(pogo_dir, name)
        attach_file_if_exists(report, log, key)
