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

import consts, cPickle, gtk, gtk.glade, os


__dirCache = {}

def listDir(directory, listHiddenFiles=False):
    """
        Return a list of tuples (filename, path) with the given directory content
        The dircache module sorts the list of files, and either it's not needed or it's not sorted the way we want
    """
    if directory in __dirCache: cachedMTime, list = __dirCache[directory]
    else:                       cachedMTime, list = None, None

    if os.path.exists(directory): mTime = os.stat(directory).st_mtime
    else:                         mTime = 0

    if mTime != cachedMTime:
        # Make sure it's readable
        if os.access(directory, os.R_OK | os.X_OK): list = os.listdir(directory)
        else:                                       list = []

        __dirCache[directory] = (mTime, list)

    return [(filename, os.path.join(directory, filename)) for filename in list if listHiddenFiles or filename[0] != '.']


def sec2str(seconds, alwaysShowHours=False):
    """ Return a formatted string based on the given duration in seconds """
    hours, seconds   = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds,   60)

    if alwaysShowHours or hours != 0: return '%u:%02u:%02u' % (hours, minutes, seconds)
    else:                             return '%u:%02u' % (minutes, seconds)


def loadGladeFile(file, root=None):
    """ Load the given Glade file and return the tree of widgets """
    if root is None: return gtk.glade.XML(os.path.join(consts.dirRes, file), domain=consts.appNameShort)
    else:            return gtk.glade.XML(os.path.join(consts.dirRes, file), root, consts.appNameShort)


def pickleLoad(file):
    """ Use cPickle to load the data structure stored in the given file """
    input = open(file, 'r')
    data  = cPickle.load(input)
    input.close()
    return data


def pickleSave(file, data):
    """ Use cPickle to save the data to the given file """
    output = open(file, 'w')
    cPickle.dump(data, output)
    output.close()


def touch(filePath):
    """ Equivalent to the Linux 'touch' command """
    os.system('touch "%s"' % filePath)


def percentEncode(string):
    """
        Percent-encode all the bytes in the given string
        I didn't find a Python method to do that
    """
    mask  = '%%%X' * len(string)
    bytes = tuple([ord(c) for c in string])

    return mask % bytes


def getCursorPosition():
    """ Return a tuple (x, y) """
    cursorNfo = gtk.gdk.display_get_default().get_pointer()
    return (cursorNfo[1], cursorNfo[2])
