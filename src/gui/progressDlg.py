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

import tools


class CancelledException(Exception):
    pass


class ProgressDlg:
    """ Display a dialog with a progress bar """

    def __init__(self, parent, primaryText, secondaryText):
        """ Contructor """
        self.parent    = parent
        self.cancelled = False
        # Widgets
        self.wTree       = tools.loadGladeFile('Progress.glade')
        self.dialog      = self.wTree.get_widget('dlg')
        self.lblCurrent  = self.wTree.get_widget('lbl-current')
        self.progressBar = self.wTree.get_widget('progress-bar')
        # GTK+ handlers
        self.wTree.get_widget('btn-cancel').connect('clicked', self.onCancel)
        # Configure and show the progress dialog
        if parent is not None:
            parent.set_sensitive(False)
            self.dialog.set_transient_for(parent)
        self.setPrimaryText(primaryText)
        self.setSecondaryText(secondaryText)
        self.dialog.set_title(tools.consts.appName)
        self.dialog.set_deletable(False)
        self.dialog.show_all()


    def destroy(self):
        """ Destroy the progress dialog """
        if self.parent is not None:
            self.parent.set_sensitive(True)
        self.dialog.hide()
        self.dialog.destroy()


    def pulse(self, txt=None):
        """
            Pulse the progress bar
            If txt is not None, change the current action to that value

            Raise CancelledException if the user has clicked on the cancel button
        """
        if self.cancelled:
            raise CancelledException()
        if txt is not None:
            self.lblCurrent.set_markup('<i>%s</i>' % txt)
        self.progressBar.pulse()


    def setPrimaryText(self, txt):
        """ Set the primary text for this progress dialog """
        self.wTree.get_widget('lbl-primary').set_markup('<b><big>%s</big></b>' % txt)


    def setSecondaryText(self, txt):
        """ Set the secondary text for this progress dialog """
        self.wTree.get_widget('lbl-secondary').set_label(txt)


    def setCancellable(self, cancellable):
        """ Enable/disable the cancel button """
        self.wTree.get_widget('btn-cancel').set_sensitive(cancellable)


    def onCancel(self, btn):
        """ The cancel button has been clicked """
        self.cancelled = True


    def hasBeenCancelled(self):
        """ Return True if the user has clicked on the cancel button """
        return self.cancelled
