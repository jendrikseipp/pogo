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

from tools   import consts, prefs
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
DEFAULT_LAST_EXPLORER = ('', '')   # Module name and explorer name


class Explorer(modules.Module):
    """ This module manages the left part of the GUI, with all the exploration stuff """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_CMD_EXPLORER_ADD, consts.MSG_CMD_EXPLORER_REMOVE, consts.MSG_CMD_EXPLORER_RENAME))
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
        """ Fill the combo box based on the internal structures """
        rows = []
        for modName in self.explorers.iterkeys():
            for (expName, (pixbuf, widget)) in self.explorers[modName].iteritems():
                rows.append((pixbuf, expName, modName, False, False))
        rows.sort(key=lambda row: (row[ROW_MODULE] + row[ROW_NAME]).lower())

        # Try to keep the same entry selected, or restore the saved one
        oldIndex = self.combo.get_active()
        if oldIndex != -1:
            (selModName, selExpName) = self.store.get(self.store.get_iter(oldIndex), ROW_MODULE, ROW_NAME)
        else:
            savedSelection = prefs.get(__name__, 'last-explorer', DEFAULT_LAST_EXPLORER)
            # Backward compatibility...
            if type(savedSelection) is tuple: (selModName, selExpName) = savedSelection
            else:                             (selModName, selExpName) = DEFAULT_LAST_EXPLORER

        self.combo.freeze_child_notify()
        self.store.clear()

        newIndex, lastModName = -1, None
        for row in rows:
            if lastModName != row[ROW_MODULE]:
                lastModName = row[ROW_MODULE]
                # Insert a separator between each different module
                if len(self.store) != 0: self.store.append((None, '', '', True, False))
                # Insert an header before each different module
                self.store.append((None, '<b>%s</b>' % lastModName, '', False, True))
            if row[ROW_MODULE] == selModName and row[ROW_NAME] == selExpName:
                newIndex = len(self.store)
            self.store.append(row)

        # Restore the previously selected index, if any
        if newIndex == -1:
            self.notebook.set_current_page(0)
            self.currExplorer = -1
        else:
            self.combo.set_active(newIndex)

        self.combo.set_sensitive(len(self.store) != 0)
        self.combo.thaw_child_notify()


    def addExplorer(self, modName, expName, pixbuf, widget):
        """ Add a new explorer to the combo box """
        if pixbuf is None:
            pixbuf = consts.icoDir

        if modName not in self.explorers: self.explorers[modName]          = {expName: (pixbuf, widget)}
        else:                             self.explorers[modName][expName] = (pixbuf, widget)

        if widget not in self.widgets:
            self.widgets[widget] = self.notebook.get_n_pages()
            self.notebook.append_page(widget)

        self.__fillComboBox()


    def delExplorer(self, modName, expName):
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


    def renameExplorer(self, modName, expName, newExpName):
        """ Rename the given explorer """
        # Beware of this special case: This screws the dictionnary
        if newExpName == expName:
            return

        try:
            # Modify the dictionnary
            self.explorers[modName][newExpName] = self.explorers[modName][expName]
            del self.explorers[modName][expName]

            # Rename the combo box entry
            for row in self.store:
                if row[ROW_NAME] == expName:
                    row[ROW_NAME] = newExpName
                    break

            # Changed the saved name if needed
            (savedModName, savedExpName) = prefs.get(__name__, 'last-explorer', (modName, expName))
            if savedModName == modName and savedExpName == expName:
                prefs.set(__name__, 'last-explorer', (modName, newExpName))
        except:
            pass


   # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this modules """
        if msg == consts.MSG_CMD_EXPLORER_ADD:
            self.addExplorer(params['modName'], params['expName'], params['icon'], params['widget'])
        elif msg == consts.MSG_CMD_EXPLORER_REMOVE:
            self.delExplorer(params['modName'], params['expName'])
        elif msg == consts.MSG_CMD_EXPLORER_RENAME:
            self.renameExplorer(params['modName'], params['expName'], params['newExpName'])


    # --== GTK handlers ==--


    def onChanged(self, combo):
        """ A new explorer has been selected with the combo box """
        currExplorer = self.combo.get_active()

        if currExplorer == -1:
            self.notebook.set_current_page(0)
        else:
            modName, expName, isHeader = self.store.get(self.store.get_iter(currExplorer), ROW_MODULE, ROW_NAME, ROW_IS_HEADER)

            if isHeader:
                if self.currExplorer is not None:
                    self.combo.set_active(self.currExplorer)
            else:
                if self.currExplorer != currExplorer:
                    self.currExplorer = currExplorer
                    prefs.set(__name__, 'last-explorer', (modName, expName))
                    modules.postMsg(consts.MSG_EVT_EXPLORER_CHANGED, {'modName': modName, 'expName': expName})

                (pixbuf, widget) = self.explorers[modName][expName]
                self.notebook.set_current_page(self.widgets[widget])
