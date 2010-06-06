# -*- coding: utf-8 -*-
#
# Author: Ingelrest François (Francois.Ingelrest@gmail.com)
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

import consts

class Logger:

    def __init__(self, filename):
        """ Constructor """
        self.handler = open(filename, 'wt')


    def __log(self, msgType, msg):
        """ Private logging function  """
        self.handler.write('%-6s %s\n' % (msgType, msg))
        self.handler.flush()


    def info(self, msg):
        """ Information message """
        self.__log('INFO', msg)


    def error(self, msg):
        """ Error message """
        self.__log('ERROR', msg)


logger = Logger(consts.fileLog)
