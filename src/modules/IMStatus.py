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

import dbus, gui, media.track, modules, traceback

from tools     import consts, prefs
from gettext   import gettext as _
from tools.log import logger

MOD_INFO = ('Instant Messenger Status', _('Instant Messenger Status'), _('Update the status message of your IM client'), [], False, True)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]


# Possible actions upon stopping or quitting
(
    STOP_DO_NOTHING,
    STOP_SET_STATUS
) = range(2)


# Default preferences
DEFAULT_STATUS_MSG       = '♫ {artist} - {album} ♫'
DEFAULT_STOP_ACTION      = STOP_SET_STATUS
DEFAULT_STOP_STATUS      = _('Decibel is stopped')
DEFAULT_SANITIZED_WORDS  = ''
DEFAULT_UPDATE_ON_PAUSED = True
DEFAULT_UPDATE_WHEN_AWAY = False


##############################################################################


class Gaim:

    def __init__(self, dbusInterface):
        """ Constructor """
        self.dbusInterface = dbusInterface


    def listAccounts(self):
        """ Return a default account """
        return ['GenericAccount']


    def setStatusMsg(self, account, msg):
        """ Change the status message of the given account """
        try:
            current    = self.dbusInterface.GaimSavedstatusGetCurrent()
            statusType = self.dbusInterface.GaimSavedstatusGetType(current)
            statusId   = self.dbusInterface.GaimPrimitiveGetIdFromType(statusType)
            if statusId == 'available' or prefs.get(__name__, 'update-when-away', DEFAULT_UPDATE_WHEN_AWAY):
                saved = self.dbusInterface.GaimSavedstatusNew('', statusType)
                self.dbusInterface.GaimSavedstatusSetMessage(saved, msg)
                self.dbusInterface.GaimSavedstatusActivate(saved)
        except:
            logger.error('[%s] Unable to set Gaim status\n\n%s' % (MOD_NAME, traceback.format_exc()))


##############################################################################


class Gajim:

    def __init__(self, dbusInterface):
        """ Constructor """
        self.dbusInterface = dbusInterface


    def listAccounts(self):
        """ Return a list of existing accounts """
        try:
            return [account for account in self.dbusInterface.list_accounts()]
        except:
            logger.error('[%s] Unable to list Gajim accounts\n\n%s' % (MOD_NAME, traceback.format_exc()))
            return []


    def setStatusMsg(self, account, msg):
        """ Change the status message of the given account """
        try:
            currentStatus = self.dbusInterface.get_status(account)
            if currentStatus in ('online', 'chat') or prefs.get(__name__, 'update-when-away', DEFAULT_UPDATE_WHEN_AWAY):
                self.dbusInterface.change_status(currentStatus, msg, account)
        except:
            logger.error('[%s] Unable to set Gajim status\n\n%s' % (MOD_NAME, traceback.format_exc()))


##############################################################################


class Gossip:

    def __init__(self, dbusInterface):
        """ Constructor """
        self.dbusInterface = dbusInterface


    def listAccounts(self):
        """ Return a default account """
        return ['GenericAccount']


    def setStatusMsg(self, account, msg):
        """ Change the status message of the given account """
        try:
            currentStatus, currentMsg = self.dbusInterface.GetPresence('')
            if currentStatus == 'available' or prefs.get(__name__, 'update-when-away', DEFAULT_UPDATE_WHEN_AWAY):
                self.dbusInterface.SetPresence(currentStatus, msg)
        except:
            logger.error('[%s] Unable to set Gossip status\n\n%s' % (MOD_NAME, traceback.format_exc()))


##############################################################################


class Pidgin:

    def __init__(self, dbusInterface):
        """ Constructor """
        self.dbusInterface = dbusInterface


    def listAccounts(self):
        """ Return a default account """
        return ['GenericAccount']


    def setStatusMsg(self, account, msg):
        """ Change the status message of the given account """
        try:
            current    = self.dbusInterface.PurpleSavedstatusGetCurrent()
            # This used to be needed, but seems to have been fixed in Pidgin
            # statusType = dbus.UInt32(self.dbusInterface.PurpleSavedstatusGetType(current))
            statusType = self.dbusInterface.PurpleSavedstatusGetType(current)
            statusId   = self.dbusInterface.PurplePrimitiveGetIdFromType(statusType)

            if statusId == 'available' or prefs.get(__name__, 'update-when-away', DEFAULT_UPDATE_WHEN_AWAY):
                saved = self.dbusInterface.PurpleSavedstatusNew('', statusType)
                self.dbusInterface.PurpleSavedstatusSetMessage(saved, msg)
                self.dbusInterface.PurpleSavedstatusActivate(saved)
        except:
            logger.error('[%s] Unable to set Pidgin status\n\n%s' % (MOD_NAME, traceback.format_exc()))


##############################################################################


# Elements associated with each supported IM clients
(
    IM_NAME,
    IM_DBUS_SERVICE_NAME,
    IM_DBUS_OBJECT_NAME,
    IM_DBUS_INTERFACE_NAME,
    IM_CLASS,
    IM_INSTANCE,
    IM_ACCOUNTS
) = range(7)


# All specific classes have been defined, so we can now populate the list of supported IM clients
CLIENTS = (
            ['Gajim',  'org.gajim.dbus',                 '/org/gajim/dbus/RemoteObject',   'org.gajim.dbus.RemoteInterface',    Gajim,  None, []],
            ['Gossip', 'org.gnome.Gossip',               '/org/gnome/Gossip',              'org.gnome.Gossip',                  Gossip, None, []],
            ['Gaim',   'net.sf.gaim.GaimService',        '/net/sf/gaim/GaimObject',        'net.sf.gaim.GaimInterface',         Gaim,   None, []],
            ['Pidgin', 'im.pidgin.purple.PurpleService', '/im/pidgin/purple/PurpleObject', 'im.pidgin.purple.PurpleInterfacep', Pidgin, None, []]
          )


class IMStatus(modules.Module):

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_NEW_TRACK,  consts.MSG_EVT_PAUSED,      consts.MSG_EVT_UNPAUSED,
                                       consts.MSG_EVT_STOPPED,    consts.MSG_EVT_APP_STARTED, consts.MSG_EVT_APP_QUIT,
                                       consts.MSG_EVT_MOD_LOADED, consts.MSG_EVT_MOD_UNLOADED))


    def init(self):
        """ Initialize the module """
        self.track     = None   # Current track
        self.status    = ''     # The currently used status
        self.paused    = False  # True if the current track is paused
        self.clients   = []     # Clients currently active
        self.cfgWindow = None   # Configuration window

        # Detect active clients
        try:
            session        = dbus.SessionBus()
            activeServices = session.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus').ListNames()
            for activeClient in [client for client in CLIENTS if client[IM_DBUS_SERVICE_NAME] in activeServices]:
                obj       = session.get_object(activeClient[IM_DBUS_SERVICE_NAME], activeClient[IM_DBUS_OBJECT_NAME])
                interface = dbus.Interface(obj, activeClient[IM_DBUS_INTERFACE_NAME])

                activeClient[IM_INSTANCE] = activeClient[IM_CLASS](interface)
                activeClient[IM_ACCOUNTS] = activeClient[IM_INSTANCE].listAccounts()

                logger.info('[%s] Found %s instance' % (MOD_NAME, activeClient[IM_NAME]))
                self.clients.append(activeClient)
        except:
            logger.error('[%s] Error while initializing\n\n%s' % (MOD_NAME, traceback.format_exc()))


    def __format(self, string, track):
        """ Replace the special fields in the given string by their corresponding value and sanitize the result """
        result = track.format(string)

        if len(prefs.get(__name__, 'sanitized-words', DEFAULT_SANITIZED_WORDS)) != 0:
            lowerResult = result.lower()
            for word in [w.lower() for w in prefs.get(__name__, 'sanitized-words', DEFAULT_SANITIZED_WORDS).split('\n') if len(w) > 2]:
                pos = lowerResult.find(word)
                while pos != -1:
                    result      = result[:pos+1] + ('*' * (len(word)-2)) + result[pos+len(word)-1:]
                    lowerResult = lowerResult[:pos+1] + ('*' * (len(word)-2)) + lowerResult[pos+len(word)-1:]
                    pos         = lowerResult.find(word)

        return result


    def setStatusMsg(self, status):
        """ Try to update the status of all accounts of all active IM clients """
        for client in self.clients:
            for account in client[IM_ACCOUNTS]:
                client[IM_INSTANCE].setStatusMsg(account, status)


    def onNewTrack(self, track):
        """ A new track is being played """
        self.track  = track
        self.status = self.__format(prefs.get(__name__, 'status-msg', DEFAULT_STATUS_MSG), track)
        self.paused = False
        self.setStatusMsg(self.status)


    def onStopped(self):
        """ The current track has been stopped """
        self.track  = None
        self.paused = False
        if prefs.get(__name__, 'stop-action', DEFAULT_STOP_ACTION) == STOP_SET_STATUS:
            self.setStatusMsg(prefs.get(__name__, 'stop-status', DEFAULT_STOP_STATUS))


    def onPaused(self):
        """ The current track has been paused """
        self.paused = True
        if prefs.get(__name__, 'update-on-paused', DEFAULT_UPDATE_ON_PAUSED):
            self.setStatusMsg(_('%(status)s [paused]') % {'status': self.status})


    def onUnpaused(self):
        """ The current track has been unpaused """
        self.paused = False
        self.setStatusMsg(self.status)


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if   msg == consts.MSG_EVT_PAUSED:       self.onPaused()
        elif msg == consts.MSG_EVT_STOPPED:      self.onStopped()
        elif msg == consts.MSG_EVT_APP_QUIT:     self.onStopped()
        elif msg == consts.MSG_EVT_UNPAUSED:     self.onUnpaused()
        elif msg == consts.MSG_EVT_NEW_TRACK:    self.onNewTrack(params['track'])
        elif msg == consts.MSG_EVT_MOD_LOADED:   self.init()
        elif msg == consts.MSG_EVT_APP_STARTED:  self.init()
        elif msg == consts.MSG_EVT_MOD_UNLOADED: self.onStopped()


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration window """
        if self.cfgWindow is None:
            self.cfgWindow = gui.window.Window('IMStatus.glade', 'vbox1', __name__, _(MOD_NAME), 440, 290)
            # GTK handlers
            self.cfgWindow.getWidget('rad-stopDoNothing').connect('toggled', self.onRadToggled)
            self.cfgWindow.getWidget('rad-stopSetStatus').connect('toggled', self.onRadToggled)
            self.cfgWindow.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWindow.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWindow.hide())
            self.cfgWindow.getWidget('btn-help').connect('clicked', self.onBtnHelp)

        if not self.cfgWindow.isVisible():
            self.cfgWindow.getWidget('txt-status').set_text(prefs.get(__name__, 'status-msg', DEFAULT_STATUS_MSG))
            self.cfgWindow.getWidget('chk-updateOnPaused').set_active(prefs.get(__name__, 'update-on-paused', DEFAULT_UPDATE_ON_PAUSED))
            self.cfgWindow.getWidget('chk-updateWhenAway').set_active(prefs.get(__name__, 'update-when-away', DEFAULT_UPDATE_WHEN_AWAY))
            self.cfgWindow.getWidget('rad-stopDoNothing').set_active(prefs.get(__name__, 'stop-action', DEFAULT_STOP_ACTION) == STOP_DO_NOTHING)
            self.cfgWindow.getWidget('rad-stopSetStatus').set_active(prefs.get(__name__, 'stop-action', DEFAULT_STOP_ACTION) == STOP_SET_STATUS)
            self.cfgWindow.getWidget('txt-stopStatus').set_sensitive(prefs.get(__name__, 'stop-action', DEFAULT_STOP_ACTION) == STOP_SET_STATUS)
            self.cfgWindow.getWidget('txt-stopStatus').set_text(prefs.get(__name__, 'stop-status', DEFAULT_STOP_STATUS))
            self.cfgWindow.getWidget('txt-sanitizedWords').get_buffer().set_text(prefs.get(__name__, 'sanitized-words', DEFAULT_SANITIZED_WORDS))
            self.cfgWindow.getWidget('btn-ok').grab_focus()

        self.cfgWindow.show()


    def onRadToggled(self, btn):
        """ A radio button has been toggled """
        self.cfgWindow.getWidget('txt-stopStatus').set_sensitive(self.cfgWindow.getWidget('rad-stopSetStatus').get_active())


    def onBtnOk(self, btn):
        """ Save new preferences """
        prefs.set(__name__, 'status-msg', self.cfgWindow.getWidget('txt-status').get_text())
        prefs.set(__name__, 'update-on-paused', self.cfgWindow.getWidget('chk-updateOnPaused').get_active())
        prefs.set(__name__, 'update-when-away', self.cfgWindow.getWidget('chk-updateWhenAway').get_active())
        (start, end) = self.cfgWindow.getWidget('txt-sanitizedWords').get_buffer().get_bounds()
        prefs.set(__name__, 'sanitized-words', self.cfgWindow.getWidget('txt-sanitizedWords').get_buffer().get_text(start, end).strip())
        if self.cfgWindow.getWidget('rad-stopDoNothing').get_active():
            prefs.set(__name__, 'stop-action', STOP_DO_NOTHING)
        else:
            prefs.set(__name__, 'stop-action', STOP_SET_STATUS)
            prefs.set(__name__, 'stop-status', self.cfgWindow.getWidget('txt-stopStatus').get_text())
        self.cfgWindow.hide()
        # Update status
        if self.track is not None:
            self.status = self.__format(prefs.get(__name__, 'status-msg', DEFAULT_STATUS_MSG), self.track)
            if self.paused: self.setStatusMsg(_('%(status)s [paused]') % {'status': self.status})
            else:           self.setStatusMsg(self.status)


    def onBtnHelp(self, btn):
        """ Display a small help message box """
        helpDlg = gui.help.HelpDlg(_(MOD_NAME))
        helpDlg.addSection(_('Description'),
                           _('This module detects any running instant messenger and updates your status with regards to the track '
                             'you are listening to. Supported messengers are:')
                           + '\n\n * ' + '\n * '.join(sorted([client[IM_NAME] for client in CLIENTS])))
        helpDlg.addSection(_('Customizing the Status'),
                           _('You can set the status to any text you want. Before setting it, the module replaces all fields of '
                             'the form {field} by their corresponding value. Available fields are:')
                           + '\n\n' + media.track.getFormatSpecialFields(False))
        helpDlg.addSection(_('Markup'),
                           _('You can use the Pango markup language to format the text. More information on that language is '
                             'available on the following web page:')
                           + '\n\nhttp://www.pygtk.org/pygtk2reference/pango-markup-language.html')
        helpDlg.addSection(_('Sanitization'),
                           _('You can define some words that to sanitize before using them to set your status. In this '
                             'case, the middle characters of matching words is automatically replaced with asterisks '
                             '(e.g., "Metallica - Live S**t Binge & Purge"). Put one word per line.'))
        helpDlg.show(self.cfgWindow)
