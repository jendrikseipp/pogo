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
import sys
import threading
import traceback
from collections import defaultdict
from os.path import splitext

if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
    sys.path.insert(0, base_dir)

import playlist

from format          import monkeysaudio, asf, flac, mp3, mp4, mpc, ogg, wavpack
from tools.log       import logger
from track.fileTrack import FileTrack
import tools


# Supported formats with associated modules
mFormats = {'.ac3': monkeysaudio, '.ape': monkeysaudio, '.flac': flac, '.m4a': mp4, '.mp2': mp3, '.mp3': mp3, '.mp4': mp4, '.mpc': mpc,'.oga': ogg, '.ogg': ogg, '.wma': asf, '.wv': wavpack}


def isSupported(file):
    """ Return True if the given file is a supported format """
    try:    return splitext(file.lower())[1] in mFormats
    except: return False


def getSupportedFormats():
    """ Return a list of all formats from which tags can be extracted """
    return ['*' + ext for ext in mFormats]



_track_cache = {}
# It seems a lock is not really necessary here. It does slow down execution
# a little bit though, so don't use it.
#_track_cache_lock = threading.Lock()

def _getTrackFromFile(file):
    """
        Return a Track object, based on the tags of the given file
        The 'file' parameter must be a real file (not a playlist or a directory)
    """
    try:
        return mFormats[splitext(file.lower())[1]].getTrack(file)
    except:
        logger.error('Unable to extract information from %s\n\n%s' % (file, traceback.format_exc()))
        return FileTrack(file)

def getTrackFromFile(file):
    """
        Return a Track object, based on the tags of the given file
        The 'file' parameter must be a real file (not a playlist or a directory)
    """
    #_track_cache_lock.acquire()
    name = os.path.basename(file)
    if file in _track_cache:
        #_track_cache_lock.release()
        return _track_cache[file]
    track = _getTrackFromFile(file)
    _track_cache[file] = track
    #_track_cache_lock.release()
    return track


def getTracksFromFiles(files):
    """ Same as getTrackFromFile(), but works on a list of files instead of a single one """
    return [getTrackFromFile(file) for file in files]


def getTracksFlat(filenames, sortByFilename=False):
    """ Same as getTracksFromFiles(), but works for any kind of filenames (files, playlists, directories) """
    allTracks = []

    # Directories
    for directory in [filename for filename in filenames if os.path.isdir(filename)]:
        mediaFiles, playlists = [], []
        for root, subdirs, files in os.walk(directory):
            for file in files:
                if isSupported(file):            mediaFiles.append(os.path.join(root, file))
                elif playlist.isSupported(file): playlists.append(os.path.join(root, file))

        if sortByFilename: allTracks.extend(sorted(getTracksFromFiles(mediaFiles), lambda t1, t2: cmp(t1.getFilePath(), t2.getFilePath())))
        else:              allTracks.extend(sorted(getTracksFromFiles(mediaFiles)))

        for pl in playlists:
            allTracks.extend(getTracksFromFiles(playlist.load(pl)))

    # Files
    tracks = getTracksFromFiles([filename for filename in filenames if os.path.isfile(filename) and isSupported(filename)])

    if sortByFilename: allTracks.extend(sorted(tracks, lambda t1, t2: cmp(t1.getFilePath(), t2.getFilePath())))
    else:              allTracks.extend(sorted(tracks))

    # Playlists
    for pl in [filename for filename in filenames if os.path.isfile(filename) and playlist.isSupported(filename)]:
        allTracks.extend(getTracksFromFiles(playlist.load(pl)))

    return allTracks



class TrackDir(object):
    def __init__(self, name='', dir=None, flat=False):
        self.dir = dir
        if name:
            self.dirname = name
        elif dir:
            self.dirname = tools.dirname(dir)
        else:
            self.dirname = 'noname'

        # If flat is True, add files without directories
        self.flat = flat

        self.tracks = []
        self.subdirs = []

    def empty(self):
        return not self.tracks and not self.subdirs

    def get_all_tracks(self):
        tracks = []
        for track in self.tracks:
            tracks.append(track)
        for subdir in self.subdirs:
            tracks.extend(subdir.get_all_tracks())
        return tracks

    def get_playtime(self):
        time = 0
        for track in self.get_all_tracks():
            time += track.getLength()
        return time

    def __len__(self):
        return len(self.get_all_tracks())

    def __str__(self, indent=0):
        res = ''
        res += '- %s\n' % self.dirname
        for track in self.tracks:
            res += (' '*indent) + '%s\n' % track
        if self.subdirs:
            for dir in self.subdirs:
                res += (' '*indent) + '%s' % dir.__str__(indent=indent+4)

        return res


def preloadTracks(paths):
    '''
    Function for preloading tracks. It is invoked when a dnd action starts
    and preloads the selected tracks in reverse order, so that the tracks are
    loaded, when the real loading function comes to them.
    '''
    for path in reversed(paths):
        if os.path.isdir(path):
            subpaths = [path for (name, path) in tools.listDir(path)]
            preloadTracks(subpaths)
        elif isSupported(path):
            getTrackFromFile(path)


def scanPaths(dir_info, name='', tracks=None):
    if tracks is None:
        tracks = defaultdict(list)

    for (subname, subpath) in dir_info:
        if os.path.isdir(subpath):
            subname = name + ' / ' + subname if name else subname
            tracks.update(scanPaths(tools.listDir(subpath), subname, tracks))
        elif isSupported(subpath):
            track = getTrackFromFile(subpath)
            tracks[name].append(track)
    return tracks


def getTracks(filenames, sortByFilename=True):
    """ Same as getTracksFromFiles(), but works for any kind of filenames (files, playlists, directories) """
    assert type(filenames) == list, 'filenames has to be a list'

    tracks = TrackDir(flat=True)

    for path in sorted(filenames):
        if os.path.isdir(path):
            dirname = tools.dirname(path)
            track_dict = scanPaths(tools.listDir(path), name=dirname)
            for name, track_list in sorted(track_dict.iteritems()):
                trackdir = TrackDir(name=name)
                trackdir.tracks = track_list
                tracks.subdirs.append(trackdir)
        elif isSupported(path):
            track = getTrackFromFile(path)
            tracks.tracks.append(track)

    return tracks



if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
    sys.path.insert(0, base_dir)

    dirs = ['/home/jendrik/tmp/Horses'] * 50

    from pprint import pprint
    dir = '/home/jendrik/tmp/Horses'
    tracks = scanPaths(tools.listDir(dir))
    for key, value in sorted(tracks.iteritems()):
        print key
        print value
        print

    tracks = getTracks(['/home/jendrik/tmp/Horses'])
    print tracks

    sys.exit()

    import timeit
    t1 = timeit.Timer("getTracks(dirs)",
                    'from __main__ import getTracks, dirs')
    print t1.timeit(1000)
