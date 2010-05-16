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

import dbus, os.path, sys, tools.consts

(CMD_ARGS, CMD_HELP, CMD_MSG) = range(3)

commands = {
                'play':    ( '',                 'Start playing the current track',             tools.consts.MSG_CMD_TOGGLE_PAUSE      ),
                'pause':   ( '',                 'Pause or continue playing the current track', tools.consts.MSG_CMD_TOGGLE_PAUSE      ),
                'next':    ( '',                 'Jump to the next track',                      tools.consts.MSG_CMD_NEXT              ),
                'prev':    ( '',                 'Jump to the previous track',                  tools.consts.MSG_CMD_PREVIOUS          ),
                'stop':    ( '',                 'Stop playback',                               tools.consts.MSG_CMD_STOP              ),
                'pl-set':  ( 'file1 file2...',   'Set the playlist to the given files',         tools.consts.MSG_CMD_TRACKLIST_SET     ),
                'pl-add':  ( 'file1 file2...',   'Append the given files to the playlist',      tools.consts.MSG_CMD_TRACKLIST_ADD     ),
                'pl-clr':  ( '',                 'Clear the playlist',                          tools.consts.MSG_CMD_TRACKLIST_CLR     ),
                'shuffle': ( '',                 'Shuffle the playlist',                        tools.consts.MSG_CMD_TRACKLIST_SHUFFLE ),
                'volume':  ( 'value (0 -- 100)', 'Set the volume',                              tools.consts.MSG_CMD_SET_VOLUME        ),
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
    print 'Command  | Arguments      | Description'
    print '-----------------------------------------------------------------------'
    for cmd, data in sorted(commands.iteritems()):
        print '%s| %s| %s' % (cmd.ljust(9), data[CMD_ARGS].ljust(17), data[CMD_HELP])
    sys.exit(1)

# Get a valid D-Bus interface
session        = dbus.SessionBus()
activeServices = session.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus').ListNames()

if not tools.consts.dbusService in activeServices:
    print '%s is not running, or D-Bus support is not available' % tools.consts.appName
    sys.exit(2)

remoteObject    = session.get_object(tools.consts.dbusService, tools.consts.dbusObject)
remoteInterface = dbus.Interface(remoteObject, tools.consts.dbusInterface)

# Send the command
if not remoteInterface.sendMsg(commands[cmdName][CMD_MSG], sys.argv[2:]):
    print '%s returned an error' % tools.consts.appName
sys.exit(0)
