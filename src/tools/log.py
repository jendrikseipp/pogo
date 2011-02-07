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

import consts


class Logger:

    def __init__(self, filename):
        """ Constructor """
        self.handler = open(filename, 'wt')
        
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
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        root_logger.addHandler(console)
        
        logging.debug('stdout logging level: %s' % level)
        logging.info('Writing log to file "%s"' % filename)


    def __log(self, msgType, msg):
        """ Private logging function  """
        self.handler.write('%-6s %s\n' % (msgType, msg))
        self.handler.flush()


    def info(self, msg):
        """ Information message """
        self.__log('INFO', msg)
        logging.info(msg)


    def error(self, msg):
        """ Error message """
        self.__log('ERROR', msg)
        logging.error(msg)


logger = Logger(consts.fileLog)
