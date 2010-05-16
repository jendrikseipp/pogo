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

import collections, gtk

from gtk     import gdk
from tools   import consts
from gobject import signal_new, TYPE_NONE, TYPE_PYOBJECT, SIGNAL_RUN_LAST


# Custom signals
signal_new('exttreeview-row-expanded',   gtk.TreeView, SIGNAL_RUN_LAST, TYPE_NONE, (TYPE_PYOBJECT,))
signal_new('exttreeview-row-collapsed',  gtk.TreeView, SIGNAL_RUN_LAST, TYPE_NONE, (TYPE_PYOBJECT,))
signal_new('exttreeview-button-pressed', gtk.TreeView, SIGNAL_RUN_LAST, TYPE_NONE, (gdk.Event, TYPE_PYOBJECT))


class ExtTreeView(gtk.TreeView):

    def __init__(self, columns, useMarkup=False):
        """ If useMarkup is True, the markup attribute will be used instead of the text one for CellRendererTexts """
        gtk.TreeView.__init__(self)

        self.selection = self.get_selection()

        # Default configuration for this tree
        self.set_headers_visible(False)
        self.selection.set_mode(gtk.SELECTION_MULTIPLE)

        # Create the columns
        nbEntries = 0
        dataTypes = []
        for (title, renderers, expandable) in columns:
            if title is None:
                for (renderer, type) in renderers:
                    nbEntries += 1
                    dataTypes.append(type)
            else:
                column = gtk.TreeViewColumn(title)
                column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
                column.set_expand(expandable)
                self.append_column(column)

                for (renderer, type) in renderers:
                    nbEntries += 1
                    dataTypes.append(type)
                    column.pack_start(renderer, False)

                    if isinstance(renderer, gtk.CellRendererText):
                        if useMarkup: column.add_attribute(renderer, 'markup', nbEntries-1)
                        else:         column.add_attribute(renderer, 'text',   nbEntries-1)
                    else:
                        column.add_attribute(renderer, 'pixbuf', nbEntries-1)

        # Create the TreeStore associated with this tree
        self.store = gtk.TreeStore(*dataTypes)
        self.set_model(self.store)

        # Drag'n'drop management
        self.dndContext      = None
        self.dndSources      = None
        self.dndStartPos     = None
        self.motionEvtId     = None
        self.isDraggableFunc = lambda: True

        self.connect('drag-begin',           self.onDragBegin)
        self.connect('row-expanded',         self.onRowExpanded)
        self.connect('row-collapsed',        self.onRowCollapsed)
        self.connect('button-press-event',   self.onButtonPressed)
        self.connect('button-release-event', self.onButtonReleased)

        # Show the tree
        self.show()


    # --== Miscellaneous ==--


    def __getSafeIter(self, path):
        """ Return None if path is None, an iter on path otherwise """
        if path is None: return None
        else:            return self.store.get_iter(path)


    def scroll(self, path):
        """ Ensure that path is visible """
        self.scroll_to_cell(path)


    def selectPaths(self, paths):
        """ Select all the given paths """
        self.selection.unselect_all()
        for path in paths:
            self.selection.select_path(path)


    # --== Retrieving content ==--


    def getCount(self):
        """ Return how many rows are stored in the tree """
        return len(self.store)


    def __len__(self):
        """ Return how many rows are stored in the tree """
        return len(self.store)


    def isValidPath(self, path):
        """ Return whether the path exists """
        try:    self.store.get_iter(path)
        except: return False

        return True


    def getRow(self, path):
        """ Return the given row """
        return tuple(self.store[path])


    def getRows(self, paths):
        """ Return the given rows """
        return [tuple(self.store[path]) for path in paths]


    def getSelectedRows(self):
        """ Return selected row(s) """
        return [tuple(self.store[path]) for path in self.selection.get_selected_rows()[1]]


    def getSelectedPaths(self):
        """ Return a list containg the selected path(s) """
        return self.selection.get_selected_rows()[1]


    def iterSelectedRows(self):
        """ Iterate on selected rows """
        for path in self.selection.get_selected_rows()[1]:
            yield tuple(self.store[path])


    def getSelectedRowsCount(self):
        """ Return how many rows are currently selected """
        return self.selection.count_selected_rows()


    def isRowSelected(self, rowPath):
        """ Return whether the given is selected """
        return self.selection.path_is_selected(rowPath)


    def getItem(self, rowPath, colIndex):
        """ Return the value of the given item """
        return self.store.get_value(self.store.get_iter(rowPath), colIndex)


    def getNbChildren(self, parentPath):
        """ Return the number of children of the given path """
        return self.store.iter_n_children(self.__getSafeIter(parentPath))


    def getChild(self, parentPath, num):
        """ Return a path to the given child, or None if none """
        child = self.store.iter_nth_child(self.__getSafeIter(parentPath), num)

        if child is None: return None
        else:             return self.store.get_path(child)


    def iterChildren(self, parentPath):
        """ Iterate on the children of the given path """
        iter = self.store.iter_children(self.__getSafeIter(parentPath))

        while iter is not None:
            yield self.store.get_path(iter)
            iter = self.store.iter_next(iter)


    # --== Adding/removing content ==--


    def replaceContent(self, rows):
        """ Replace the content of the list with the given rows """
        parent = self.__getSafeIter(None)
        self.freeze_child_notify()
        self.set_model(None)
        self.store.clear()
        for row in rows:
            self.store.append(parent, row)
        self.set_model(self.store)
        self.thaw_child_notify()


    def clear(self):
        """ Remove all rows from the tree """
        self.store.clear()


    def appendRow(self, row, parentPath=None):
        """ Append a row to the tree """
        return self.store.get_path(self.store.append(self.__getSafeIter(parentPath), row))


    def appendRows(self, rows, parentPath=None):
        """ Append some rows to the tree """
        parent = self.__getSafeIter(parentPath)
        self.freeze_child_notify()
        for row in rows:
            self.store.append(parent, row)
        self.thaw_child_notify()


    def insertRowBefore(self, row, parentPath, siblingPath):
        """ Insert a row as a child of parent before siblingPath """
        self.store.insert_before(self.__getSafeIter(parentPath), self.store.get_iter(siblingPath), row)


    def insertRowAfter(self, row, parentPath, siblingPath):
        """ Insert a row as a child of parent after siblingPath """
        self.store.insert_after(self.__getSafeIter(parentPath), self.store.get_iter(siblingPath), row)


    def removeRow(self, rowPath):
        """ Remove the given row """
        self.store.remove(self.store.get_iter(rowPath))


    def removeAllChildren(self, rowPath):
        """ Remove all the children of the given row """
        self.freeze_child_notify()
        while self.getNbChildren(rowPath) != 0:
            self.removeRow(self.getChild(rowPath, 0))
        self.thaw_child_notify()


    def setItem(self, rowPath, colIndex, value):
        """ Change the value of the given item """
        self.store.set_value(self.store.get_iter(rowPath), colIndex, value)


    # --== Changing the state of nodes ==--


    def expandRow(self, path):
        """ Expand the given row """
        self.expand_row(path, False)


    def expandRows(self, paths=None):
        """ Expand the given rows, or the selected rows if paths is None """
        if paths is None:
            paths = self.getSelectedPaths()

        for path in paths:
            self.expand_row(path, False)


    def collapseRows(self, paths=None):
        """ Collapse the given rows, or the selected rows if paths is None """
        if paths is None:
            paths = self.getSelectedPaths()

        for path in paths:
            self.collapse_row(path)


    def switchRows(self, paths=None):
        """ Collapse expanded/expand collapsed given rows, or the selected rows if paths is None """
        if paths is None:
            paths = self.getSelectedPaths()

        for path in paths:
            if self.row_expanded(path): self.collapse_row(path)
            else:                       self.expand_row(path, False)


    # --== D'n'D management ==--


    def setIsDraggableFunc(self, isDraggableFunc):
        """ The function must return True is the selected rows can be dragged, False otherwise """
        self.isDraggableFunc = isDraggableFunc


    def setDNDSources(self, sources):
        """ Define which kind of D'n'D this tree will generate """
        self.dndSources = sources


    # --== Saving/restoring the current state of the tree ==--


    def saveState(self, nameIndex):
        """
            Return a structure representing the current state of the tree
            The nameIndex parameter is the index of the value that stores rows' name
        """
        queue         = collections.deque((None,))
        expandedNodes = []

        while len(queue) != 0:
            for row in self.iterChildren(queue.pop()):
                if self.row_expanded(row):
                    queue.append(row)
                    expandedNodes.append((row, self.getRow(row)[nameIndex]))

        return (self.get_visible_range(), self.selection.get_selected_rows()[1], expandedNodes)


    def restoreState(self, state, nameIndex):
        """ Try to restore the given state, saved with saveState() """
        (visibleRange, selectedRows, expandedNodes) = state

        for (row, name) in expandedNodes:
            if self.isValidPath(row) and self.getRow(row)[nameIndex] == name and not self.row_expanded(row):
                self.expand_row(row, False)

        if visibleRange is not None:
            self.scroll(visibleRange[0])

        for path in selectedRows:
            self.selection.select_path(path)


    # --== GTK Handlers ==--


    def onRowExpanded(self, tree, iter, path):
        """ A row has been expanded """
        self.emit('exttreeview-row-expanded', path)


    def onRowCollapsed(self, tree, iter, path):
        """ A row has been collapsed """
        self.emit('exttreeview-row-collapsed', path)


    def onButtonPressed(self, tree, event):
        """ A mouse button has been pressed """
        retVal   = False
        pathInfo = self.get_path_at_pos(int(event.x), int(event.y))

        if pathInfo is None: path = None
        else:                path = pathInfo[0]

        if event.button == 1 or event.button == 3:
            if path is None:
                self.selection.unselect_all()
            else:
                if event.button == 1 and self.motionEvtId is None:
                    self.dndStartPos = (int(event.x), int(event.y))
                    self.motionEvtId = gtk.TreeView.connect(self, 'motion-notify-event', self.onMouseMotion)

                stateClear = not (event.state & (gdk.SHIFT_MASK | gdk.CONTROL_MASK))

                if stateClear and not self.selection.path_is_selected(path):
                    self.selection.unselect_all()
                    self.selection.select_path(path)
                else:
                    retVal = (stateClear and self.getSelectedRowsCount() > 1 and self.selection.path_is_selected(path))

        self.emit('exttreeview-button-pressed', event, path)

        return retVal


    def onButtonReleased(self, tree, event):
        """ A mouse button has been released """
        if self.motionEvtId is not None:
            self.disconnect(self.motionEvtId)
            self.dndContext  = None
            self.motionEvtId = None

        stateClear = not (event.state & (gdk.SHIFT_MASK | gdk.CONTROL_MASK))

        if stateClear and event.state & gdk.BUTTON1_MASK and self.getSelectedRowsCount() > 1:
            pathInfo = self.get_path_at_pos(int(event.x), int(event.y))
            if pathInfo is not None:
                self.selection.unselect_all()
                self.selection.select_path(pathInfo[0])


    def onMouseMotion(self, tree, event):
        """ The mouse has been moved """
        if self.dndContext is None and self.isDraggableFunc() and self.dndSources is not None:
            if self.drag_check_threshold(self.dndStartPos[0], self.dndStartPos[1], int(event.x), int(event.y)):
                self.dndContext = self.drag_begin(self.dndSources, gdk.ACTION_COPY, 1, event)


    def onDragBegin(self, tree, context):
        """ A drag'n'drop operation has begun """
        if self.getSelectedRowsCount() == 1: context.set_icon_stock(gtk.STOCK_DND,          0, 0)
        else:                                context.set_icon_stock(gtk.STOCK_DND_MULTIPLE, 0, 0)
