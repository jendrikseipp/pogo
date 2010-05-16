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

import gtk, gui, tools

from tools   import consts, prefs
from base64  import b64encode, b64decode
from gettext import gettext as _


# The dialog used for authentication
mBtnOk     = None
mAuthDlg   = None
mChkStore  = None
mTxtLogin  = None
mTxtPasswd = None


__keyring = None


def __loadKeyring():
    """ Load the keyring if needed """
    global __keyring

    import gnomekeyring as gk

    if __keyring is None:
        __keyring = gk.get_default_keyring_sync()
        if __keyring is None:
            __keyring = 'login'


def __loadAuthInfo(id):
    """ Load the login/password associated with id, either from the Gnome keyring or from the prefs """
    try:
        import gnomekeyring as gk

        useGK = True
    except:
        useGK = False

    # No Gnome keyring
    if not useGK:
        login  = prefs.get(__name__, id + '_login',  None)
        passwd = prefs.get(__name__, id + '_passwd', None)

        if login is not None and passwd is not None: return (login, b64decode(passwd))
        else:                                        return None

    # From here we can use the Gnome keyring
    __loadKeyring()

    try:                          gk.create_sync(__keyring, None)
    except gk.AlreadyExistsError: pass

    token = prefs.get(__name__, id + '_gkToken', None)
    if token is not None:
        try:
            login, passwd = gk.item_get_info_sync(__keyring, token).get_secret().split('\n')
            return (login, passwd)
        except:
            pass

    return None


def __storeAuthInfo(id, login, passwd):
    """ Store the login/password associated with id, either in the Gnome keyring or in the prefs """
    try:
        import gnomekeyring as gk

        useGK = True
    except:
        useGK = False

    # No Gnome keyring
    if not useGK:
        prefs.set(__name__, id + '_login',  login)
        prefs.set(__name__, id + '_passwd', b64encode(passwd))  # Pretty useless, but the user prefers not to see his password as clear text
        return

    # From here we can use the Gnome keyring
    __loadKeyring()

    try:
        label    = '%s (%s)' % (consts.appName, id)
        authInfo = '\n'.join((login, passwd))
        token    = gk.item_create_sync(__keyring, gk.ITEM_GENERIC_SECRET, label, {'appName': consts.appName, 'id': id}, authInfo, True)
        prefs.set(__name__, id + '_gkToken', token)
    except:
        pass


def getAuthInfo(id, reason, defaultLogin=None, force=False, parent=None):
    """
        The parameter id may be any arbitrary string, but it must be unique as it identifies the login information given by the user.
        If a {login/password} is already known for this identifier, it is immediately returned without asking anything to the user.
        If no login is currently known, ask the user for the authentication information.
    """
    global mBtnOk, mAuthDlg, mChkStore, mTxtLogin, mTxtPasswd

    if not force:
        authInfo = __loadAuthInfo(id)
        if authInfo is not None:
            return authInfo

    if mAuthDlg is None:
        wTree      = tools.loadGladeFile('Authentication.glade')
        mBtnOk     = wTree.get_widget('btn-ok')
        mAuthDlg   = wTree.get_widget('dlg-main')
        mChkStore  = wTree.get_widget('chk-store')
        mTxtLogin  = wTree.get_widget('txt-login')
        mTxtPasswd = wTree.get_widget('txt-passwd')

        wTree.get_widget('lbl-reason').set_text(_('Enter your username and password for\n%(reason)s') % {'reason': reason})
        wTree.get_widget('dlg-action_area').set_child_secondary(wTree.get_widget('btn-help'), True)   # Glade fails to do that
        wTree.get_widget('lbl-title').set_markup('<big><big><big><b>%s</b></big></big></big>' % _('Password required'))

        mAuthDlg.set_title(consts.appName)
        mAuthDlg.resize_children()
        mAuthDlg.connect('response',  onResponse)
        mTxtLogin.connect('changed',  lambda entry: mBtnOk.set_sensitive(mTxtLogin.get_text() != '' and mTxtPasswd.get_text() != ''))
        mTxtPasswd.connect('changed', lambda entry: mBtnOk.set_sensitive(mTxtLogin.get_text() != '' and mTxtPasswd.get_text() != ''))

    if defaultLogin is not None:
        mTxtLogin.set_text(defaultLogin)
        mTxtPasswd.set_text('')
        mTxtPasswd.grab_focus()
    else:
        mTxtLogin.set_text('')
        mTxtPasswd.set_text('')
        mTxtLogin.grab_focus()

    mBtnOk.set_sensitive(False)
    mAuthDlg.show_all()
    respId = mAuthDlg.run()
    mAuthDlg.hide()

    if respId == gtk.RESPONSE_OK:
        login  = mTxtLogin.get_text()
        passwd = mTxtPasswd.get_text()

        if mChkStore.get_active():
            __storeAuthInfo(id, login, passwd)

        return (login, passwd)

    return None


def onResponse(dlg, respId):
    """ One of the button in the dialog box has been clicked """
    if respId == gtk.RESPONSE_HELP:
        primary   = _('About password storage safety')
        secondary = '%s\n\n%s' % (_('If you use Gnome, it is safe to store your password since the Gnome keyring is used.'),
                                  _('If you do not use Gnome, beware that, although not stored as clear text, an attacker <i>could</i> retrieve it.'))
        gui.infoMsgBox(dlg, primary, secondary)
        dlg.stop_emission('response')
