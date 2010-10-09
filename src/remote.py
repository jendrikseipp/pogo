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

import dbus, os.path, sys

(
    PLAY,
    PAUSE,
    NEXT,
    PREVIOUS,
    STOP,
    SET,
    ADD,
    CLEAR,
    SHUFFLE,
    VOLUME,
) = range(10)

(CMD_ARGS, CMD_HELP, CMD_NAME) = range(3)

commands = {
                'play':    ( '',                 'Start playing the current track',             PLAY    ),
                'pause':   ( '',                 'Pause or continue playing the current track', PAUSE   ),
                'next':    ( '',                 'Jump to the next track',                      NEXT    ),
                'prev':    ( '',                 'Jump to the previous track',                  PREVIOUS),
                'stop':    ( '',                 'Stop playback',                               STOP    ),
                'pl-set':  ( 'file1 file2...',   'Set the playlist to the given files',         SET     ),
                'pl-add':  ( 'file1 file2...',   'Append the given files to the playlist',      ADD     ),
                'pl-clr':  ( '',                 'Clear the playlist',                          CLEAR   ),
                'shuffle': ( '',                 'Shuffle the playlist',                        SHUFFLE ),
                'volume':  ( 'value (0 -- 100)', 'Set the volume',                              VOLUME  ),
           }

# Check the command line
cmdLineOk = False

if len(sys.argv) > 1:
    cmdName = sys.argv[1]

    if cmdName not in commands:                                    print '%s is not a valid command\n'     % cmdName
    elif len(sys.argv) == 2 and commands[cmdName][CMD_ARGS] != '': print '%s needs some arguments\n'       % cmdName
    elif len(sys.argv) > 2 and commands[cmdName][CMD_ARGS] == '':  print '%s does not take any argument\n' % cmdName
    else:                                                          cmdLineOk = True

if not cmdLineOk:
    print 'Usage: %s command [arg1 arg2...]\n' % os.path.basename(sys.argv[0])
    print 'Command  | Arguments        | Description'
    print '-------------------------------------------------------------------------'
    for cmd, data in sorted(commands.iteritems()):
        print '%s| %s| %s' % (cmd.ljust(9), data[CMD_ARGS].ljust(17), data[CMD_HELP])
    sys.exit(1)

# Connect to D-BUS
session        = dbus.SessionBus()
activeServices = session.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus').ListNames()

if 'org.mpris.pogo' not in activeServices:
    print 'Pogo is not running, or D-Bus support is not available'
    sys.exit(2)

cmd       = commands[cmdName][CMD_NAME]
player    = dbus.Interface(session.get_object('org.mpris.pogo', '/Player'),    'org.freedesktop.MediaPlayer')
tracklist = dbus.Interface(session.get_object('org.mpris.pogo', '/TrackList'), 'org.freedesktop.MediaPlayer')

if   cmd == SET:      tracklist.SetTracks(sys.argv[2:], True)
elif cmd == ADD:
    print 'Hello'
    tracklist.AddTracks(sys.argv[2:], False)
elif cmd == PLAY:     player.Play()
elif cmd == NEXT:     player.Next()
elif cmd == STOP:     player.Stop()
elif cmd == PAUSE:    player.Pause()
elif cmd == CLEAR:    tracklist.Clear()
elif cmd == VOLUME:   player.VolumeSet(int(sys.argv[2]))
elif cmd == SHUFFLE:  tracklist.SetRandom(True)
elif cmd == PREVIOUS: player.Prev()
