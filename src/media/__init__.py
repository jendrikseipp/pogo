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

import os
import sys

if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
    sys.path.insert(0, base_dir)

import playlist, traceback

from format          import monkeysaudio, asf, flac, mp3, mp4, mpc, ogg, wavpack
from os.path         import splitext
from tools.log       import logger
from track.fileTrack import FileTrack


# Supported formats with associated modules
mFormats = {'.ac3': monkeysaudio, '.ape': monkeysaudio, '.flac': flac, '.m4a': mp4, '.mp2': mp3, '.mp3': mp3, '.mp4': mp4, '.mpc': mpc,'.oga': ogg, '.ogg': ogg, '.wma': asf, '.wv': wavpack}


def isSupported(file):
    """ Return True if the given file is a supported format """
    try:    return splitext(file.lower())[1] in mFormats
    except: return False


def getSupportedFormats():
    """ Return a list of all formats from which tags can be extracted """
    return ['*' + ext for ext in mFormats]


def getTrackFromFile(file):
    """
        Return a Track object, based on the tags of the given file
        The 'file' parameter must be a real file (not a playlist or a directory)
    """
    try:
        return mFormats[splitext(file.lower())[1]].getTrack(file)
    except:
        logger.error('Unable to extract information from %s\n\n%s' % (file, traceback.format_exc()))
        return FileTrack(file)


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
    

class TrackDir(object):
    def __init__(self, name='', dir=None, flat=False):
        self.dir = dir
        if name:
            self.dirname = name
        elif dir:
            self.dirname = dirname(dir)
        else:
            self.dirname = 'noname'
        
        # If flat is True, add files without directories
        self.flat = flat
        
        self.tracks = []
        self.subdirs = []
        
        if dir and not flat:
            self.scan()
        
    def scan(self):
        import tools
        for filename, path in sorted(tools.listDir(self.dir)):
            if os.path.isdir(path):
                trackdir = TrackDir(dir=path)
                # Only add subdirs that contain songs
                if trackdir.tracks or trackdir.subdirs:
                    self.subdirs.append(trackdir)
            elif isSupported(filename):
                track = getTrackFromFile(path)
                self.tracks.append(track)
                
            # If a directory contains no tracks and only one subdir, 
            # collapse them into one dir
            if not self.tracks and len(self.subdirs) == 1:
                subdir = self.subdirs.pop(0)
                self.tracks = subdir.tracks
                self.dirname += ' / ' + subdir.dirname
                
    def empty(self):
        return not self.tracks and not self.subdirs
        
    def iter_all_tracks(self):
        for track in self.tracks:
            yield track
        for subdir in self.subdirs:
            subdir.iter_all_tracks()
        
    def __len__(self):
        return len(list(self.iter_all_tracks()))        
                
    def __str__(self, indent=0):
        res = ''
        res += '- %s\n' % self.dirname
        for track in self.tracks:
            res += (' '*indent) + '%s\n' % track
        if self.subdirs:
            for dir in self.subdirs:
                res += (' '*indent) + '%s' % dir.__str__(indent=indent+4)
            
        return res
        
    
def getTracks(filenames, sortByFilename=False):
    """ Same as getTracksFromFiles(), but works for any kind of filenames (files, playlists, directories) """
    assert type(filenames) == list, 'filenames has to be a list'
    
    tracks = TrackDir(flat=True)
    
    for path in sorted(filenames):
        if os.path.isdir(path):
            trackdir = TrackDir(dir=path)
            tracks.subdirs.append(trackdir)
        elif isSupported(path):
            track = getTrackFromFile(path)
            tracks.tracks.append(track)
            
    print 'SCANNED TRACKS', tracks
            
    return tracks
    
    
if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
    sys.path.insert(0, base_dir)
    
    print dirname('/home/')
    print dirname('/home/dir')
    print dirname('/home/dir/..')
    print dirname('/')
    
    dir = getTracks(['/home/jendrik/tmp/Elbow - The Seldom Seen Kid (2008)/'])
    print dir
