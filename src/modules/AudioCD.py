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

import cgi, gobject, gtk, gui, modules, os, socket, tools, traceback, urllib

from gui                 import extTreeview
from tools               import consts, icons, prefs, sec2str
from gettext             import gettext as _
from tools.log           import logger
from media.track.cdTrack import CDTrack

MOD_INFO = ('Audio CD', _('Audio CD'), _('Play audio discs'), ('DiscID', 'CDDB'), False, True)

MOD_L10N             = MOD_INFO[modules.MODINFO_L10N]
PREFS_DFT_DEVICE     = '/dev/cdrom'
PREFS_DFT_USE_CDDB   = True
PREFS_DFT_USE_CACHE  = True
PREFS_DFT_READ_SPEED = 1


# Format of a row in the treeview
(
    ROW_PIXBUF,
    ROW_LENGTH,
    ROW_NAME,
    ROW_TRACK
) = range(4)


# All CD-ROM read speeds
READ_SPEEDS = {
                 1 :  0,
                 2 :  1,
                 4 :  2,
                 8 :  3,
                10 :  4,
                12 :  5,
                20 :  6,
                32 :  7,
                36 :  8,
                40 :  9,
                48 : 10,
                50 : 11,
                52 : 12,
                56 : 13,
                72 : 14,
              }


# Information returned by disc_id()
DISC_FRAME1    =  2
DISC_FRAMEn    = -2
DISC_LENGTH    = -1
DISC_CHECKSUM  =  0
DISC_NB_TRACKS =  1


class AudioCD(modules.ThreadedModule):

    def __init__(self):
        """ Constructor """
        modules.ThreadedModule.__init__(self, (consts.MSG_EVT_APP_QUIT,    consts.MSG_EVT_MOD_LOADED, consts.MSG_EVT_EXPLORER_CHANGED,
                                               consts.MSG_EVT_APP_STARTED, consts.MSG_EVT_MOD_UNLOADED))


    def onModLoaded(self):
        """ The module has been loaded """
        txtRdrLen = gtk.CellRendererText()

        columns = (('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf), (txtRdrLen, gobject.TYPE_STRING), (gtk.CellRendererText(), gobject.TYPE_STRING)], True),
                   (None, [(None, gobject.TYPE_PYOBJECT)],                                                                                               False))

        # The album length is written in a smaller font, with a lighter color
        txtRdrLen.set_property('scale', 0.85)
        txtRdrLen.set_property('foreground', '#909090')

        self.tree     = extTreeview.ExtTreeView(columns, True)
        self.popup    = None
        self.cfgWin   = None
        self.expName  = MOD_L10N
        self.scrolled = gtk.ScrolledWindow()
        self.cacheDir = os.path.join(consts.dirCfg, MOD_INFO[modules.MODINFO_NAME])
        # Explorer
        self.tree.setDNDSources([consts.DND_TARGETS[consts.DND_DAP_TRACKS]])
        self.scrolled.add(self.tree)
        self.scrolled.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled.show()
        # GTK handlers
        self.tree.connect('drag-data-get',              self.onDragDataGet)
        self.tree.connect('key-press-event',            self.onKeyPressed)
        self.tree.connect('exttreeview-button-pressed', self.onButtonPressed)
        modules.postMsg(consts.MSG_CMD_EXPLORER_ADD, {'modName': MOD_L10N, 'expName': self.expName, 'icon': icons.cdromMenuIcon(), 'widget': self.scrolled})
        # Hide the album length when not drawing the root node
        self.tree.get_column(0).set_cell_data_func(txtRdrLen, self.__drawAlbumLenCell)
        # CD-ROM drive read speed
        modules.postMsg(consts.MSG_CMD_SET_CD_SPEED, {'speed': prefs.get(__name__, 'read-speed', PREFS_DFT_READ_SPEED)})


    def __drawAlbumLenCell(self, column, cell, model, iter):
        """ Use a different background color for alphabetical headers """
        if model.get_value(iter, ROW_LENGTH) is None: cell.set_property('visible', False)
        else:                                         cell.set_property('visible', True)


    def onModUnloaded(self):
        """ The module is going to be unloaded """
        modules.postMsg(consts.MSG_CMD_EXPLORER_REMOVE, {'modName': MOD_L10N, 'expName': MOD_L10N})
        if not prefs.get(__name__, 'use-cache', PREFS_DFT_USE_CACHE):
            self.clearCache()


    def getTracksFromPaths(self, tree, paths):
        """
            Return a list of tracks with all the associated tags:
                * From the list 'paths' if it is not None
                * From the current selection if 'paths' is None
        """
        if paths is None:
            if tree.isRowSelected((0,)): return [tree.getItem(child, ROW_TRACK) for child in tree.iterChildren((0,))]
            else:                        return [row[ROW_TRACK] for row in tree.getSelectedRows()]
        else:
            if (0,) in paths: return [tree.getItem(child, ROW_TRACK) for child in tree.iterChildren((0,))]
            else:             return [row[ROW_TRACK] for row in tree.getRows(paths)]


    def playPaths(self, tree, paths, replace):
        """
            Replace/extend the tracklist
            If the list 'paths' is None, use the current selection
        """
        if self.tree.getNbChildren((0,)) != 0:
            tracks = self.getTracksFromPaths(tree, paths)

            if replace: modules.postMsg(consts.MSG_CMD_TRACKLIST_SET, {'tracks': tracks, 'playNow': True})
            else:       modules.postMsg(consts.MSG_CMD_TRACKLIST_ADD, {'tracks': tracks})


    # --== Cache management ==--


    def clearCache(self):
        """ Clear cache content """
        for file in os.listdir(self.cacheDir):
            os.remove(os.path.join(self.cacheDir, file))


    def isDiscInCache(self, discInfo):
        """ Return whether the given disc is present in the cache """
        return os.path.exists(os.path.join(self.cacheDir, str(discInfo[DISC_CHECKSUM])))


    def getDiscFromCache(self, discInfo):
        """ Return CDDB information from the cache, or None if that disc is not cached """
        try:    return tools.pickleLoad(os.path.join(self.cacheDir, str(discInfo[DISC_CHECKSUM])))
        except: return None


    def addDiscToCache(self, discInfo, cddb):
        """ Add the given CDDB information to the cache """
        if not os.path.exists(self.cacheDir):
            os.mkdir(self.cacheDir)

        try:    tools.pickleSave(os.path.join(self.cacheDir, str(discInfo[DISC_CHECKSUM])), cddb)
        except: pass


    # --== Gui management, these functions must be executed in the GTK main loop ==--


    def createTree(self, nbTracks):
        """ Create a temporary explorer tree without disc information """
        name = '%s  <span size="smaller" foreground="#909090">%s</span>' % (MOD_L10N, _('downloading data...'))
        self.tree.replaceContent(((icons.cdromMenuIcon(), None, name, None),))

        # Append a child for each track
        self.tree.appendRows([(icons.mediaFileMenuIcon(), None, _('Track %02u') % (i+1), None) for i in xrange(nbTracks)], (0,))
        self.tree.expand_all()


    def updateTree(self, discInfo):
        """ Update the tree using disc information from the cache, if any """
        cddb = self.getDiscFromCache(discInfo)

        # Create fake CDDB information if needed
        if cddb is None:
            cddb = {'DTITLE': '%s / %s' % (consts.UNKNOWN_ARTIST, consts.UNKNOWN_ALBUM)}
            for i in xrange(discInfo[DISC_NB_TRACKS]):
                cddb['TTITLE%u' % i] = consts.UNKNOWN_TITLE

        # Compute the length of each track
        trackLen = [int(round((discInfo[DISC_FRAME1 + i + 1] - discInfo[DISC_FRAME1 + i]) / 75.0)) for i in xrange(discInfo[DISC_NB_TRACKS] - 1)]
        trackLen.append(discInfo[DISC_LENGTH] - int(round(discInfo[DISC_FRAMEn] / 75.0)))

        # Update the root of the tree
        disc          = cddb['DTITLE'].strip().decode('iso-8859-15', 'replace')
        artist, album = disc.split(' / ')

        self.tree.setItem((0,), ROW_NAME, '%s' % cgi.escape(disc))
        self.tree.setItem((0,), ROW_LENGTH, '[%s]' % sec2str(sum(trackLen)))

        # Update the explorer name
        modules.postMsg(consts.MSG_CMD_EXPLORER_RENAME, {'modName': MOD_L10N, 'expName': self.expName, 'newExpName': disc})
        self.expName = disc

        # Optional information
        try:    date = int(cddb['DYEAR'].strip().decode('iso-8859-15', 'replace'))
        except: date = None

        try:    genre = cddb['DGENRE'].strip().decode('iso-8859-15', 'replace')
        except: genre = None

        # Update each track
        for i, child in enumerate(self.tree.iterChildren((0,))):
            title = cddb['TTITLE%u' % i].strip().decode('iso-8859-15', 'replace')

            # Create the corresponding Track object
            track = CDTrack(str(i+1))
            track.setTitle(title)
            track.setAlbum(album)
            track.setArtist(artist)
            track.setLength(trackLen[i])
            track.setNumber(i+1)
            # Optional information
            if date is not None:  track.setDate(date)
            if genre is not None: track.setGenre(genre)
            # Fill the tree
            self.tree.setItem(child, ROW_NAME, '%02u. %s' % (i + 1, cgi.escape(title)))
            self.tree.setItem(child, ROW_TRACK, track)


    # --== Disc management ==--


    def cddbRequest(self, discInfo):
        """ Return disc information from online CDDB, None if request fails """
        import CDDB

        # Make sure to not be blocked by the request
        socket.setdefaulttimeout(consts.socketTimeout)

        try:
            (status, info) = CDDB.query(discInfo)

            if   status == 200: disc = info       # Success
            elif status == 210: disc = info[0]    # Exact multiple matches
            elif status == 211: disc = info[0]    # Inexact multiple matches
            else:               raise Exception, 'Unknown disc (phase 1 returned %u)' % status

            (status, info) = CDDB.read(disc['category'], disc['disc_id'])

            if status == 210: return info
            else:             raise Exception, 'Unknown disc (phase 2 returned %u)' % status
        except:
            logger.error('[%s] CDDB request failed\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))
            return None


    def loadDisc(self):
        """ Read disc information and create the explorer tree accordingly """
        import DiscID

        try:
            discInfo = DiscID.disc_id(DiscID.open(prefs.get(__name__, 'device', PREFS_DFT_DEVICE)))
        except Exception, err:
            if err[0] == 123:
                self.tree.replaceContent([(icons.cdromMenuIcon(), None, _('No disc found'), None)])
                modules.postMsg(consts.MSG_CMD_EXPLORER_RENAME, {'modName': MOD_L10N, 'expName': self.expName, 'newExpName': MOD_L10N})
                self.expName = MOD_L10N
            else:
                logger.error('[%s] Unable to read device\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))
            return

        # Create a temporary tree, download CDDB information if needed, and update the tree
        gobject.idle_add(self.createTree, discInfo[DISC_NB_TRACKS])
        if not self.isDiscInCache(discInfo) and prefs.get(__name__, 'use-cddb', PREFS_DFT_USE_CDDB):
            cddb = self.cddbRequest(discInfo)
            if cddb is not None:
                self.addDiscToCache(discInfo, cddb)
        gobject.idle_add(self.updateTree, discInfo)


    def reloadDisc(self):
        """ Reload the disc """
        # Sort of hack, to be sure that the reloading is done in the thread's code and not in the GTK main loop
        self.postMsg(consts.MSG_EVT_EXPLORER_CHANGED, {'modName': MOD_L10N, 'expName': self.expName})


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_MOD_LOADED or msg == consts.MSG_EVT_APP_STARTED:
            self.onModLoaded()
        elif msg == consts.MSG_EVT_MOD_UNLOADED or msg == consts.MSG_EVT_APP_QUIT:
            self.onModUnloaded()
        elif msg == consts.MSG_EVT_EXPLORER_CHANGED and params['modName'] == MOD_L10N:
            self.loadDisc()


    # --== GTK handlers ==--


    def onDragDataGet(self, tree, context, selection, info, time):
        """ Provide information about the data being dragged """
        serializedTracks = '\n'.join([track.serialize() for track in self.getTracksFromPaths(tree, None)])
        selection.set(consts.DND_TARGETS[consts.DND_DAP_TRACKS][0], 8, serializedTracks)


    def onShowPopupMenu(self, tree, button, time, path):
        """ Show a popup menu """
        if self.popup is None:
            self.popup = tools.loadGladeFile('AudioCDMenu.glade')
            self.popup.get_widget('menu-popup').show_all()
            self.popup.get_widget('item-add').connect('activate',     lambda widget: self.playPaths(tree, None, False))
            self.popup.get_widget('item-play').connect('activate',    lambda widget: self.playPaths(tree, None, True))
            self.popup.get_widget('item-refresh').connect('activate', lambda widget: self.reloadDisc())

        # Enable/disable menu entries depending on whether there is something to play
        if self.tree.getNbChildren((0,)) == 0:
            self.popup.get_widget('item-add').set_sensitive(False)
            self.popup.get_widget('item-play').set_sensitive(False)
        else:
            self.popup.get_widget('item-add').set_sensitive(True)
            self.popup.get_widget('item-play').set_sensitive(True)

        self.popup.get_widget('menu-popup').popup(None, None, None, button, time)


    def onButtonPressed(self, tree, event, path):
        """ A mouse button has been pressed """
        if event.button == 3:
            self.onShowPopupMenu(tree, event.button, event.time, path)
        elif path is not None:
            if event.button == 2:
                self.playPaths(tree, [path], False)
            elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                self.playPaths(tree, None, True)


    def onKeyPressed(self, tree, event):
        """ A key has been pressed """
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'F5':       self.reloadDisc()
        elif keyname == 'plus':   tree.expandRows()
        elif keyname == 'Left':   tree.collapseRows()
        elif keyname == 'Right':  tree.expandRows()
        elif keyname == 'minus':  tree.collapseRows()
        elif keyname == 'space':  tree.switchRows()
        elif keyname == 'Return': self.playPaths(tree, None, True)


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration window """
        if self.cfgWin is None:
            self.cfgWin = gui.window.Window('AudioCD.glade', 'vbox1', __name__, MOD_L10N, 335, 270)
            self.cfgWin.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWin.getWidget('btn-help').connect('clicked', self.onBtnHelp)
            self.cfgWin.getWidget('chk-useCDDB').connect('toggled', self.onUseCDDBToggled)
            self.cfgWin.getWidget('btn-clearCache').connect('clicked', self.onBtnClearCache)
            self.cfgWin.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWin.hide())

            # Set up the combo box
            combo = self.cfgWin.getWidget('combo-read-speed')
            txtRenderer = gtk.CellRendererText()
            combo.pack_start(txtRenderer, True)
            combo.add_attribute(txtRenderer, 'text', 0)
            combo.set_sensitive(True)
            txtRenderer.set_property('xpad', 6)
            # Setup the liststore
            store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_INT)
            combo.set_model(store)
            for speed in sorted(READ_SPEEDS.iterkeys()):
                store.append(('%ux' % speed, speed))

        if not self.cfgWin.isVisible():
            self.cfgWin.getWidget('btn-ok').grab_focus()
            self.cfgWin.getWidget('txt-device').set_text(prefs.get(__name__, 'device', PREFS_DFT_DEVICE))
            self.cfgWin.getWidget('chk-useCDDB').set_active(prefs.get(__name__, 'use-cddb', PREFS_DFT_USE_CDDB))
            self.cfgWin.getWidget('chk-useCache').set_sensitive(prefs.get(__name__, 'use-cddb', PREFS_DFT_USE_CDDB))
            self.cfgWin.getWidget('chk-useCache').set_active(prefs.get(__name__, 'use-cache', PREFS_DFT_USE_CACHE))
            self.cfgWin.getWidget('combo-read-speed').set_active(READ_SPEEDS[prefs.get(__name__, 'read-speed', PREFS_DFT_READ_SPEED)])

        self.cfgWin.show()


    def onUseCDDBToggled(self, useCDDB):
        """ Toggle the "use cache" checkbox according to the state of the "use CDDB" one """
        self.cfgWin.getWidget('chk-useCache').set_sensitive(useCDDB.get_active())


    def onBtnClearCache(self, btn):
        """ Clear CDDB cache """
        text     = _('This will remove all disc information stored on your hard drive.')
        question = _('Clear CDDB cache?')

        if gui.questionMsgBox(self.cfgWin, question, text) == gtk.RESPONSE_YES:
            self.clearCache()


    def onBtnOk(self, btn):
        """ Check that entered information is correct before saving everything """
        device    = self.cfgWin.getWidget('txt-device').get_text()
        useCDDB   = self.cfgWin.getWidget('chk-useCDDB').get_active()
        useCache  = useCDDB and self.cfgWin.getWidget('chk-useCache').get_active()
        readSpeed = self.cfgWin.getWidget('combo-read-speed').get_model()[self.cfgWin.getWidget('combo-read-speed').get_active()][1]

        if not os.path.exists(device):
            error    = _('Invalid path')
            errorMsg = _('The path to the CD-ROM device is not valid. Please choose an existing path.')
            gui.errorMsgBox(self.cfgWin, error, errorMsg)
            self.cfgWin.getWidget('txt-device').grab_focus()
        else:
            prefs.set(__name__, 'device',     device)
            prefs.set(__name__, 'use-cddb',   useCDDB)
            prefs.set(__name__, 'use-cache',  useCache)
            prefs.set(__name__, 'read-speed', readSpeed)
            self.cfgWin.hide()

            # CD-ROM drive read speed
            modules.postMsg(consts.MSG_CMD_SET_CD_SPEED, {'speed': readSpeed})


    def onBtnHelp(self, btn):
        """ Display a small help message box """
        helpDlg = gui.help.HelpDlg(MOD_L10N)
        helpDlg.addSection(_('Description'),
                           _('This module lets you play audio discs from your CD-ROM device.'))
        helpDlg.addSection(_('Compact Disc Data Base (CDDB)'),
                           _('Disc information, such as artist and album title, may be automatically downloaded '
                             'from an online database if you wish so. This information may also be saved on your '
                             'hard drive to avoid downloading it again the next time you play the same disc.'))
        helpDlg.show(self.cfgWin)
