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

import base64, gui, media, modules, traceback, urllib, urllib2

from gui       import authentication
from tools     import consts, prefs
from gettext   import gettext as _
from tools.log import logger


MOD_INFO = ('Twitter', 'Twitter', _('Update the status of your Twitter account'), [], False, True)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]

DEFAULT_STATUS_MSG = '♫ Listening to {album} by {artist} ♫'


class Twitter(modules.ThreadedModule):
    """ This module updates the status of a Twitter account based on the current track """

    def __init__(self):
        """ Constructor """
        modules.ThreadedModule.__init__(self, (consts.MSG_EVT_APP_STARTED, consts.MSG_EVT_MOD_LOADED, consts.MSG_EVT_NEW_TRACK))


    def onModLoaded(self):
        """ The module has been loaded """
        self.login      = None
        self.passwd     = None
        self.cfgWindow  = None
        self.lastStatus = ''


    def getAuthInfo(self):
        """ Retrieve the login/password of the user """
        auth = authentication.getAuthInfo('Twitter', _('your Twitter account'))

        if auth is None: self.login, self.passwd = None, None
        else:            self.login, self.passwd = auth


    def onNewTrack(self, track):
        """ A new track has started """
        status = track.format(prefs.get(__name__, 'status-msg', DEFAULT_STATUS_MSG))
        if status == self.lastStatus:
            return

        self.gtkExecute(self.getAuthInfo)
        if self.passwd is None:
            return

        authToken       = base64.b64encode(self.login + ':' + self.passwd)
        self.passwd     = None
        self.lastStatus = status

        request = urllib2.Request('http://twitter.com/statuses/update.xml')
        request.headers['Authorization'] = 'Basic ' + authToken
        request.data = urllib.urlencode({'status': status})

        try:
            urllib2.urlopen(request)
        except:
            logger.error('[%s] Unable to set Twitter status\n\n%s' % (MOD_NAME, traceback.format_exc()))


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_NEW_TRACK:
            self.onNewTrack(params['track'])
        elif msg == consts.MSG_EVT_APP_STARTED or msg == consts.MSG_EVT_MOD_LOADED:
            self.onModLoaded()


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration window """
        if self.cfgWindow is None:
            self.cfgWindow = gui.window.Window('Twitter.glade', 'vbox1', __name__, _(MOD_NAME), 440, 141)
            # GTK handlers
            self.cfgWindow.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWindow.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWindow.hide())
            self.cfgWindow.getWidget('btn-help').connect('clicked', self.onBtnHelp)

        if not self.cfgWindow.isVisible():
            self.cfgWindow.getWidget('txt-status').set_text(prefs.get(__name__, 'status-msg', DEFAULT_STATUS_MSG))
            self.cfgWindow.getWidget('btn-ok').grab_focus()

        self.cfgWindow.show()


    def onBtnOk(self, btn):
        """ Save new preferences """
        prefs.set(__name__, 'status-msg', self.cfgWindow.getWidget('txt-status').get_text())
        self.cfgWindow.hide()


    def onBtnHelp(self, btn):
        """ Display a small help message box """
        helpDlg = gui.help.HelpDlg(_(MOD_NAME))
        helpDlg.addSection(_('Description'),
                           _('This module posts a message to your Twitter account according to what '
                             'you are listening to.'))
        helpDlg.addSection(_('Customizing the Status'),
                           _('You can set the status to any text you want. Before setting it, the module replaces all fields of '
                             'the form {field} by their corresponding value. Available fields are:')
                           + '\n\n' + media.track.getFormatSpecialFields(False))
        helpDlg.show(self.cfgWindow)
