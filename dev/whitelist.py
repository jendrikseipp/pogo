import os.path
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
SRC_DIR = os.path.join(BASE_DIR, "src")

sys.path.insert(0, SRC_DIR)

from modules import Covers, CtrlPanel, DBus, DesktopNotification, Equalizer, \
    FileExplorer, GnomeMediaKeys, GSTPlayer, Search, StatusbarTitlebar, \
    TrackLoader, TrackPanel, Tracktree

Covers.Covers
CtrlPanel.CtrlPanel
DBus.DBus
DesktopNotification.DesktopNotification
Equalizer.Equalizer
FileExplorer.FileExplorer
GnomeMediaKeys.GnomeMediaKeys
GSTPlayer.GSTPlayer
Search.Search
StatusbarTitlebar.StatusbarTitlebar
TrackLoader.TrackLoader
TrackPanel.TrackPanel
Tracktree.Tracktree

from modules.DBus import DBusObjectRoot, DBusObjectTracklist, DBusObjectPlayer

dbor = DBusObjectRoot
dbor.Identity
dbor.Quit
dbor.MprisVersion

dbot = DBusObjectTracklist
dbot.GetMetadata
dbot.GetCurrentTrack
dbot.GetLength
dbot.AddTrack
dbot.DelTrack
dbot.SetLoop
dbot.SetRandom
dbot.Clear
dbot.SetTracks

dbop = DBusObjectPlayer
dbop.Next
dbop.Prev
dbop.Pause
dbop.Stop
dbop.Play
dbop.Repeat
dbop.GetStatus
dbop.GetCaps
dbop.PositionSet
dbop.PositionGet
