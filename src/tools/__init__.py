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

import os
import re
import cPickle
import subprocess
import codecs
import logging
from xml.sax.saxutils import escape, unescape

import gtk
import gtk.glade

import consts


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
        if os.access(directory, os.R_OK | os.X_OK):
            list = sorted(os.listdir(directory), key=lambda file: file.lower())
        else:
            list = []

        __dirCache[directory] = (mTime, list)

    return [(filename, os.path.join(directory, filename)) for filename in list if listHiddenFiles or filename[0] != '.']


def makedirs(dir):
    """
    mkdir variant that does not complain when the dir already exists
    """
    try:
        os.makedirs(dir)
    except OSError:
        # directory probably exists
        pass


def remove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def samefile(path1, path2):
    if not os.path.exists(path1) or not os.path.exists(path2):
        return False
    return os.path.samefile(path1, path2)


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
        Couldn't find a Python method to do that
    """
    mask  = '%%%X' * len(string)
    bytes = tuple([ord(c) for c in string])

    return mask % bytes


def htmlEscape(string):
    """ Replace characters &, <, and > by their equivalent HTML code """
    return escape(string)


def htmlUnescape(s):
    '''
    Unescape '&amp;', '&lt;', and '&gt;' in a string of data.
    '''
    return unescape(s)


def dirname(dir):
    '''
    returns the last dirname in path
    '''
    dir = os.path.abspath(dir)
    # Remove double slashes and last slash
    dir = os.path.normpath(dir)

    dirname, basename = os.path.split(dir)
    # Return "/" if journal is located at /
    return basename or dirname


def resize(w_old, h_old, max_width, max_height):
    '''
    Resize image dimensions keeping the original ratio
    '''
    ratio = float(w_old) / float(h_old)
    w_new = min([w_old, max_width])
    h_new = w_new / ratio
    if h_new > max_height:
        h_new = max_height
        w_new = ratio * h_new
    w_new, h_new = int(w_new), int(h_new)
    assert w_new <= max_width, '%s <= %s' % (w_new, max_width)
    assert h_new <= max_height, '%s <= %s' % (h_new, max_height)
    #assert round(ratio, 3) == round(w_new / h_new, 3), '%s == %s / %s == %s ' % (ratio, w_new, h_new, w_new / h_new)
    return (w_new, h_new)


def open_path(path):
    """ Show containing folder in default file browser """
    if os.name == 'mac':
        subprocess.call(('open', path))
    elif os.name == 'nt':
        subprocess.call(('start', path))
    elif os.name == 'posix':
        subprocess.call(('xdg-open', path))
    else:
        import webbrowser
        webbrowser.open(path)


def get_regex(string):
    quantifiers = ['?', '*']
    pattern = re.escape(unicode(string))
    for quantifier in quantifiers:
        pattern = pattern.replace('\\' + quantifier, '.' + quantifier)
    return re.compile(pattern, re.IGNORECASE)

def read_file(filename):
    """Tries to read a given file"""
    try:
        # codecs.open returns a file object that can write unicode objects
        # and whose read() method also returns unicode objects
        # Internally we want to have unicode only
        with codecs.open(filename, 'rb', encoding='utf-8', errors='replace') as file:
            data = file.read()
            return data
    except Exception, e:
        logging.error('Error while reading "%s": %s' % (filename, e))
    return ''

def write_file(filename, content):
    assert os.path.isabs(filename), filename
    try:
        with codecs.open(filename, 'wb', errors='replace', encoding='utf-8') as file:
            file.write(content)
        logging.info('Wrote file "%s"' % filename)
    except IOError, e:
        logging.error('Error while writing to "%s": %s' % (filename, e))

