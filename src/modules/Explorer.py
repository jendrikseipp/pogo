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

MOD_INFO = ('Explorer', 'Explorer', '', [], True, False)

# The rows in the combo box
(
    ROW_PIXBUF,
    ROW_NAME,
    ROW_MODULE,
    ROW_IS_SEPARATOR,
    ROW_IS_HEADER
) = range(5)


# Default preferences
DEFAULT_LAST_EXPLORER = ('', '')     # Module name and explorer name


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
        self.combo        = prefs.getWidgetsTree().get_widget('combo-explorer')
        self.widgets      = {}
        self.notebook     = prefs.getWidgetsTree().get_widget('notebook-explorer')
        self.explorers    = {}
        self.currExplorer = None
        # Setup the combo box
        txtRenderer = gtk.CellRendererText()
        pixRenderer = gtk.CellRendererPixbuf()

        self.combo.pack_start(pixRenderer, False)
        self.combo.add_attribute(pixRenderer, 'pixbuf', ROW_PIXBUF)
        self.combo.pack_start(txtRenderer, True)
        self.combo.add_attribute(txtRenderer, 'markup', ROW_NAME)
        self.combo.set_sensitive(False)
        self.combo.set_row_separator_func(lambda model, iter: model.get_value(iter, ROW_IS_SEPARATOR))
        self.combo.set_cell_data_func(txtRenderer, self.__cellDataFunction)
        txtRenderer.set_property('xpad', 6)
        # Setup the liststore
        self.store = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)
        self.combo.set_model(self.store)
        # Setup the notebook
        label = gtk.Label(_('Please select an explorer\nin the combo box below.'))
        label.show()
        self.notebook.append_page(label)
        # GTK handlers
        self.combo.connect('changed', self.onChanged)


    def __cellDataFunction(self, comboBox, cellRenderer, model, iter):
        """ Use a different format for headers """
        if model.get_value(iter, ROW_IS_HEADER): cellRenderer.set_property('xalign', 0.5)
        else:                                    cellRenderer.set_property('xalign', 0.0)


    def __fillComboBox(self):
        """ Fill the combo box """
        idx = self.combo.get_active()

        if idx == -1: (selectedModule, selectedExplorer) = prefs.get(__name__, 'last-explorer', DEFAULT_LAST_EXPLORER)
        else:         (selectedModule, selectedExplorer) = self.store.get(self.store.get_iter(idx), ROW_MODULE, ROW_NAME)

        restoredIdx = None
        self.combo.freeze_child_notify()
        self.store.clear()

        for module in sorted(self.explorers):
            self.store.append((None, '<b>%s</b>' % module, '', False, True))
            for (explorer, (pixbuf, widget)) in sorted(self.explorers[module].iteritems()):
                self.store.append((pixbuf, explorer, module, False, False))

                if module == selectedModule and explorer == selectedExplorer:
                    restoredIdx = len(self.store) - 1

        if restoredIdx is None:
            self.notebook.set_current_page(0)
            self.currExplorer = -1
        else:
            self.combo.set_active(restoredIdx)

        self.combo.set_sensitive(len(self.store) != 0)
        self.combo.thaw_child_notify()


    # --== Message handlers ==--


    def onAddExplorer(self, modName, expName, icon, widget):
        """ Add a new explorer to the combo box """
        if icon is None:
            icon = icons.dirMenuIcon()

        if modName not in self.explorers: self.explorers[modName]          = {expName: (icon, widget)}
        else:                             self.explorers[modName][expName] = (icon, widget)

        if widget not in self.widgets:
            self.widgets[widget] = self.notebook.get_n_pages()
            self.notebook.append_page(widget)

        self.__fillComboBox()


    def onRemoveExplorer(self, modName, expName):
        """ Remove an existing explorer from the combo box """
        (pixbuf, widget) = self.explorers[modName][expName]
        del self.explorers[modName][expName]

        delWidget = True
        for (expName, (pixbuf, widget2)) in self.explorers[modName].iteritems():
            if widget2 is widget:
                delWidget = False
                break

        if delWidget:
            numPage = self.widgets[widget]
            del self.widgets[widget]
            self.notebook.remove_page(numPage)
            for (widget, numPage2) in self.widgets.iteritems():
                if numPage2 > numPage:
                    self.widgets[widget] = numPage2 - 1

        self.__fillComboBox()


    def onRenameExplorer(self, modName, expName, newExpName):
        """ Rename the given explorer """
        # Beware of this special case: This screws the dictionnary
        if newExpName == expName:
            return

        # Modify the dictionnary
        self.explorers[modName][newExpName] = self.explorers[modName][expName]
        del self.explorers[modName][expName]

        # If the explorer we're renaming is currently selected, we need to rename the row
        # Otherwise, __fillComboBox() won't be able to keep it selected
        idx = self.combo.get_active()
        if idx != -1:
            (selModName, selExpName) = self.store.get(self.store.get_iter(idx), ROW_MODULE, ROW_NAME)
            if selModName == modName and selExpName == expName:
                self.store.set(self.store.get_iter(idx), ROW_NAME, newExpName)

        # This is needed to sort the explorers according to the new name
        self.__fillComboBox()

        # Changed the saved name if needed
        (savedModName, savedExpName) = prefs.get(__name__, 'last-explorer', (modName, expName))
        if savedModName == modName and savedExpName == expName:
            prefs.set(__name__, 'last-explorer', (modName, newExpName))


    # --== GTK handlers ==--


    def onChanged(self, combo):
        """ A new explorer has been selected with the combo box """
        currExplorer = combo.get_active()

        if currExplorer == -1:
            self.notebook.set_current_page(0)
        else:
            modName, expName, isHeader = self.store.get(self.store.get_iter(currExplorer), ROW_MODULE, ROW_NAME, ROW_IS_HEADER)

            if isHeader:
                if self.currExplorer is not None:
                    combo.set_active(self.currExplorer)
            else:
                if self.currExplorer != currExplorer:
                    self.currExplorer = currExplorer
                    prefs.set(__name__, 'last-explorer', (modName, expName))
                    modules.postMsg(consts.MSG_EVT_EXPLORER_CHANGED, {'modName': modName, 'expName': expName})

                (pixbuf, widget) = self.explorers[modName][expName]
                self.notebook.set_current_page(self.widgets[widget])
