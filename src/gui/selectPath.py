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

import fileChooser, gtk, gui, os.path, tools

from gettext import gettext as _


class SelectPath:

    def __init__(self, title, parent, forbiddenNames=[], forbiddenChars=[]):
        """ Constructor """
        wTree               = tools.loadGladeFile('SelectPath.glade')
        self.btnOk          = wTree.get_widget('btn-ok')
        self.dialog         = wTree.get_widget('dlg')
        self.txtName        = wTree.get_widget('txt-name')
        self.txtPath        = wTree.get_widget('txt-path')
        self.btnOpen        = wTree.get_widget('btn-open')
        self.forbiddenNames = forbiddenNames
        self.forbiddenChars = forbiddenChars

        self.dialog.set_title(title)
        self.dialog.set_transient_for(parent)

        # Handlers
        self.btnOpen.connect('clicked', self.onBtnOpen)
        self.txtName.connect('changed', self.onTxtFieldChanged)
        self.txtPath.connect('changed', self.onTxtFieldChanged)
        self.dialog.connect('response', self.onCheckDlgResponse)


    def setNameSelectionEnabled(self, enabled):
        """ Enable/disable path selection """
        self.txtName.set_sensitive(enabled)


    def setPathSelectionEnabled(self, enabled):
        """ Enable/disable path selection """
        self.txtPath.set_sensitive(enabled)
        self.btnOpen.set_sensitive(enabled)


    def run(self, defaultName='', defaultPath=''):
        """ Return a tuple (name, path) or None if the user cancelled the dialog """
        self.btnOk.set_sensitive(False)
        self.txtName.set_text(defaultName)
        self.txtPath.set_text(defaultPath)
        self.txtName.grab_focus()
        self.dialog.show_all()

        result = None
        if self.dialog.run() == gtk.RESPONSE_OK:
            result = (self.txtName.get_text(), self.txtPath.get_text())

        self.dialog.hide()
        return result


    # --== GTK handlers ==--


    def onBtnOpen(self, btn):
        """ Let the user choose a folder, and fill the corresponding field in the dialog """
        path = fileChooser.openDirectory(self.dialog, _('Choose a folder'))
        if path is not None:
            self.txtPath.set_text(path)


    def onTxtFieldChanged(self, txtEntry):
        """ Enable/disable the OK button based on the content of the text fields """
        self.btnOk.set_sensitive(self.txtName.get_text() != '' and self.txtPath.get_text() != '')


    def onCheckDlgResponse(self, dialog, response, *args):
        """ Prevent clicking on the OK button if values are not correct """
        if response == gtk.RESPONSE_OK:
            name = self.txtName.get_text()
            path = self.txtPath.get_text()

            if not os.path.isdir(path):
                gui.errorMsgBox(dialog, _('This path does not exist'), _('Please select an existing directory.'))
                dialog.stop_emission('response')
            elif name in self.forbiddenNames:
                gui.errorMsgBox(dialog, _('The name is incorrect'), _('This name is not allowed.\nPlease use another one.'))
                dialog.stop_emission('response')
            else:
                for ch in name:
                    if ch in self.forbiddenChars:
                        gui.errorMsgBox(dialog, _('The name is incorrect'), _('The character %s is not allowed.\nPlease use another name.') % ch)
                        dialog.stop_emission('response')
                        break
