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

import gui, modules, os.path

from media   import track
from tools   import consts, prefs
from gettext import gettext as _

MOD_INFO = ('Status File', _('Status File'), _('Generate a text file with the current status'), [], False, True)
MOD_L10N = MOD_INFO[modules.MODINFO_L10N]


# Default preferences
PREFS_DEFAULT_FILE   = os.path.join(consts.dirCfg, 'now-playing.txt')
PREFS_DEFAULT_STATUS = 'Now playing {title}\nby {artist}'


class StatusFile(modules.ThreadedModule):
    """ Allow external programs to display the current status """

    def __init__(self):
        """ Constructor """
        modules.ThreadedModule.__init__(self, (consts.MSG_EVT_NEW_TRACK,    consts.MSG_EVT_STOPPED,
                                               consts.MSG_EVT_MOD_UNLOADED, consts.MSG_EVT_APP_QUIT))
        self.cfgWindow = None


    def configure(self, parent):
        """ Show the configuration window """
        if self.cfgWindow is None:
            self.cfgWindow = gui.window.Window('StatusFile.glade', 'vbox1', __name__, MOD_L10N, 355, 345)
            self.btnOk     = self.cfgWindow.getWidget('btn-ok')
            self.txtFile   = self.cfgWindow.getWidget('txt-file')
            self.txtStatus = self.cfgWindow.getWidget('txt-status')
            # GTK handlers
            self.btnOk.connect('clicked', self.onOk)
            self.cfgWindow.getWidget('btn-help').connect('clicked', self.onHelp)
            self.cfgWindow.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWindow.hide())
            self.cfgWindow.getWidget('btn-open').connect('clicked', self.onOpen)

        # Fill current preferences
        if not self.cfgWindow.isVisible():
            self.txtFile.set_text(prefs.get(__name__, 'file', PREFS_DEFAULT_FILE))
            self.txtStatus.get_buffer().set_text(prefs.get(__name__, 'status', PREFS_DEFAULT_STATUS))
            self.btnOk.grab_focus()

        self.cfgWindow.show()


    def updateFile(self, track):
        """ Show the notification based on the given track """
        output = open(prefs.get(__name__, 'file', PREFS_DEFAULT_FILE), 'w')

        if track is None: output.write('')
        else:             output.write(track.format(prefs.get(__name__, 'status', PREFS_DEFAULT_STATUS)))

        output.close()


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_NEW_TRACK:
            self.updateFile(params['track'])
        elif msg == consts.MSG_EVT_STOPPED or msg == consts.MSG_EVT_APP_QUIT or msg == consts.MSG_EVT_MOD_UNLOADED:
            self.updateFile(None)


    # --== GTK handlers ==--


    def onOk(self, btn):
        """ Save the new preferences """
        if not os.path.isdir(os.path.dirname(self.txtFile.get_text())):
            gui.errorMsgBox(self.cfgWindow, _('Invalid path'), _('The path to the selected file is not valid. Please choose an existing path.'))
            self.txtFile.grab_focus()
        else:
            prefs.set(__name__, 'file', self.txtFile.get_text())
            (start, end) = self.txtStatus.get_buffer().get_bounds()
            prefs.set(__name__, 'status', self.txtStatus.get_buffer().get_text(start, end))
            self.cfgWindow.hide()


    def onOpen(self, btn):
        """ Let the user choose a file """
        dir    = os.path.dirname(self.txtFile.get_text())
        file   = os.path.basename(self.txtFile.get_text())
        result = gui.fileChooser.save(self.cfgWindow, _('Choose a file'), file, dir)

        if result is not None:
            self.txtFile.set_text(result)


    def onHelp(self, btn):
        """ Display a small help message box """
        helpDlg = gui.help.HelpDlg(MOD_L10N)
        helpDlg.addSection(_('Description'),
                           _('This module generates a text file with regards to the track currently played.'))
        helpDlg.addSection(_('Customizing the File'),
                           _('You can change the content of the file to any text you want. Before generating the file, '
                             'fields of the form {field} are replaced by their corresponding value. '
                             'Available fields are:\n\n') + track.getFormatSpecialFields(False))
        helpDlg.show(self.cfgWindow)
