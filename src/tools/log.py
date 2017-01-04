# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
# Copyright (c) 2010  Jendrik Seipp (jendrikseipp@web.de)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import sys
import logging

from . import consts


class Logger:
    def __init__(self, filename):
        """ Constructor """
        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.DEBUG)

        # Python adds a default handler if some log is generated before here
        # Remove all handlers that have been added automatically
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

        level = logging.DEBUG
        # define a Handler which writes "level" messages or higher to sys.stdout
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        # define a Handler which writes "level" messages or higher to a file
        logfile = logging.FileHandler(filename)
        logfile.setLevel(level)
        # set a log format
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        # tell the handlers to use this format
        console.setFormatter(formatter)
        logfile.setFormatter(formatter)
        # add the handlers to the root logger
        root_logger.addHandler(console)
        root_logger.addHandler(logfile)

        logging.debug('stdout logging level: %s' % level)
        logging.info('Writing log to file "%s"' % filename)

    def info(self, msg):
        """ Information message """
        logging.info(msg)

    def error(self, msg):
        """ Error message """
        logging.error(msg)


logger = Logger(consts.fileLog)
