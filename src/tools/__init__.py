# -*- coding: utf-8 -*-
#
# Authors: Ingelrest François (Francois.Ingelrest@gmail.com)
#          Jendrik Seipp (jendrikseipp@web.de)
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


__downloadCache = {}


def cleanupDownloadCache():
    """ Remove temporary downloaded files """
    for (cachedTime, file) in __downloadCache.itervalues():
        try:    os.remove(file)
        except: pass


def downloadFile(url, cacheTimeout=3600):
    """
        If the file has been in the cache for less than 'cacheTimeout' seconds, return the cached file
        Otherwise download the file and cache it

        Return a tuple (errorMsg, data) where data is None if an error occurred, errorMsg containing the error message in this case
    """
    import socket, tempfile, time, urllib2

    if url in __downloadCache: cachedTime, file = __downloadCache[url]
    else:                      cachedTime, file = -cacheTimeout, None

    now = int(time.time())

    # If the timeout is not exceeded, get the data from the cache
    if (now - cachedTime) <= cacheTimeout:
        try:
            input = open(file, 'rb')
            data  = input.read()
            input.close()

            return ('', data)
        except:
            # If something went wrong with the cache, proceed to download
            pass

    # Make sure to not be blocked by the request
    socket.setdefaulttimeout(consts.socketTimeout)

    try:
        # Retrieve the data
        request = urllib2.Request(url)
        stream  = urllib2.urlopen(request)
        data    = stream.read()

        # Do we need to create a new temporary file?
        if file is None:
            handle, file = tempfile.mkstemp()
            os.close(handle)

        # On first file added to the cache, we register our clean up function
        if len(__downloadCache) == 0:
            import atexit
            atexit.register(cleanupDownloadCache)

        __downloadCache[url] = (now, file)

        output = open(file, 'wb')
        output.write(data)
        output.close()

        return ('', data)
    except urllib2.HTTPError, err:
        return ('The request failed with error code %u' % err.code, None)
    except:
        return ('The request failed', None)

    return ('Unknown error', None)


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


def getCursorPosition():
    """ Return a tuple (x, y) """
    cursorNfo = gtk.gdk.display_get_default().get_pointer()
    return (cursorNfo[1], cursorNfo[2])


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
