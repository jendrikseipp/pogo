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

import os, threading, tools


# Load user preferences from the disk
try:    __usrPrefs = tools.pickleLoad(tools.consts.filePrefs)
except: __usrPrefs = {}

__mutex      = threading.Lock() # Prevent concurrent calls to functions
__appGlobals = {}               # Some global values shared by all the components of the application


def save():
    """ Save user preferences to the disk """
    __mutex.acquire()
    tools.pickleSave(tools.consts.filePrefs, __usrPrefs)
    os.chmod(tools.consts.filePrefs, 0600)
    __mutex.release()


def set(module, name, value):
    """ Change the value of a preference """
    __mutex.acquire()
    __usrPrefs[module + '_' + name] = value;
    __mutex.release()


def get(module, name, default=None):
    """ Retrieve the value of a preference """
    __mutex.acquire()
    try:    value = __usrPrefs[module + '_' + name]
    except: value = default
    __mutex.release()
    return value


# Command line used to start the application
def setCmdLine(cmdLine): __appGlobals['cmdLine'] = cmdLine
def getCmdLine():        return __appGlobals['cmdLine']


# Main widgets' tree created by Glade
def setWidgetsTree(tree): __appGlobals['wTree'] = tree
def getWidgetsTree():     return __appGlobals['wTree']
