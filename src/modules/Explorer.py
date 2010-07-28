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

import gobject, gtk, modules

from tools   import consts, icons, prefs
from gettext import gettext as _

MOD_INFO              = ('Explorer', 'Explorer', '', [], True, False)
DEFAULT_LAST_EXPLORER = ('', '')     # Module name and explorer name

# The rows in the combo box
(
    ROW_PIXBUF,         # Icon displayed in front of the entry
    ROW_NAME,           # Name of the entry
    ROW_MODULE,         # Name of the module the entry is associated to
    ROW_PAGE_NUM,       # Number of the notebook page the entry is associated to
    ROW_IS_HEADER,      # True if the entry is an header (used to separate different modules)
) = range(5)


class Explorer(modules.Module):
    """ This module manages the left part of the GUI, with all the exploration stuff """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, {
                                           consts.MSG_CMD_EXPLORER_ADD:    self.onAddExplorer,
                                           consts.MSG_CMD_EXPLORER_REMOVE: self.onRemoveExplorer,
                                           consts.MSG_CMD_EXPLORER_RENAME: self.onRenameExplorer,
                                      })

        # Attributes
        self.store           = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_BOOLEAN)
        self.combo           = prefs.getWidgetsTree().get_widget('combo-explorer')
        txtRenderer          = gtk.CellRendererText()
        pixRenderer          = gtk.CellRendererPixbuf()
        self.timeout         = None
        self.notebook        = prefs.getWidgetsTree().get_widget('notebook-explorer')
        self.allExplorers    = {}
        self.notebookPages   = {}
        self.currExplorerIdx = 0
        # Setup the combo box
        txtRenderer.set_property('xpad', 6)
        self.combo.pack_start(pixRenderer, False)
        self.combo.add_attribute(pixRenderer, 'pixbuf', ROW_PIXBUF)
        self.combo.pack_start(txtRenderer, True)
        self.combo.add_attribute(txtRenderer, 'markup', ROW_NAME)
        self.combo.set_sensitive(False)
        self.combo.set_cell_data_func(txtRenderer, self.__cellDataFunction)
        self.combo.set_model(self.store)
        # Setup the notebook
        label = gtk.Label(_('Please select an explorer\nin the combo box below.'))
        label.show()
        self.notebook.append_page(label)
        # GTK handlers
        self.combo.connect('changed', self.onChanged)


    def __cellDataFunction(self, combo, renderer, model, iter):
        """ Use a different format for headers """
        if model.get_value(iter, ROW_IS_HEADER): renderer.set_property('xalign', 0.5)
        else:                                    renderer.set_property('xalign', 0.0)


    def __fillComboBox(self):
        """ Fill the combo box """
        idx            = self.combo.get_active()
        restoredIdx    = None
        self.timeout   = None
        previousModule = None

        if idx == -1: selectedModule, selectedExplorer = prefs.get(__name__, 'last-explorer', DEFAULT_LAST_EXPLORER)
        else:         selectedModule, selectedExplorer = self.store[idx][ROW_MODULE], self.store[idx][ROW_NAME]

        self.combo.freeze_child_notify()
        self.store.clear()

        for (module, explorer), (pixbuf, widget) in sorted(self.allExplorers.iteritems()):

            if module != previousModule:
                self.store.append((None, '<b>%s</b>' % module, '', -1, True))
                previousModule = module

            self.store.append((pixbuf, explorer, module, self.notebookPages[widget], False))

            if module == selectedModule and explorer == selectedExplorer:
                restoredIdx = len(self.store) - 1

        if restoredIdx is None:
            self.currExplorerIdx = 0
            self.notebook.set_current_page(0)
        else:
            self.combo.set_active(restoredIdx)

        self.combo.set_sensitive(len(self.store) != 0)
        self.combo.thaw_child_notify()

        return False


    def fillComboBox(self):
        """
            Wrapper function for __fillComboBox()
            Call fillComboBox() after a small timeout, to avoid many (useless) consecutive calls to __fillComboBox()
        """
        if self.timeout is not None:
            gobject.source_remove(self.timeout)

        self.timeout = gobject.timeout_add(100, self.__fillComboBox)


    # --== Message handlers ==--


    def onAddExplorer(self, modName, expName, icon, widget):
        """ Add a new explorer to the combo box """
        if widget not in self.notebookPages:
            self.notebookPages[widget] = self.notebook.append_page(widget)

        self.allExplorers[(modName, expName)] = (icon, widget)
        self.fillComboBox()


    def onRemoveExplorer(self, modName, expName):
        """ Remove an existing explorer from the combo box """
        del self.allExplorers[(modName, expName)]
        self.fillComboBox()


    def onRenameExplorer(self, modName, expName, newExpName):
        """ Rename the given explorer """
        if newExpName != expName:
            self.allExplorers[(modName, newExpName)] = self.allExplorers[(modName, expName)]
            del self.allExplorers[(modName, expName)]

            # If the explorer we're renaming is currently selected, we need to rename the row
            # Otherwise, fillComboBox() won't be able to keep it selected
            idx = self.combo.get_active()
            if idx != -1 and self.store[idx][ROW_MODULE] == modName and self.store[idx][ROW_NAME] == expName:
                self.store[idx][ROW_NAME] = newExpName
                prefs.set(__name__, 'last-explorer', (modName, newExpName))

            self.fillComboBox()


    # --== GTK handlers ==--


    def onChanged(self, combo):
        """ A new explorer has been selected with the combo box """
        idx = combo.get_active()

        if idx == -1:
            self.notebook.set_current_page(0)
        elif self.store[idx][ROW_IS_HEADER]:
            combo.set_active(self.currExplorerIdx)
        else:
            self.currExplorerIdx = idx
            prefs.set(__name__, 'last-explorer', (self.store[idx][ROW_MODULE], self.store[idx][ROW_NAME]))
            modules.postMsg(consts.MSG_EVT_EXPLORER_CHANGED, {'modName': self.store[idx][ROW_MODULE], 'expName': self.store[idx][ROW_NAME]})
            self.notebook.set_current_page(self.store[idx][ROW_PAGE_NUM])
