# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
# Copyright (c) 2010  Jendrik Seipp (jendrikseipp@web.de)
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

import sys, os

import gtk
import gobject
from gobject import signal_new, TYPE_INT, TYPE_STRING, TYPE_PYOBJECT, TYPE_NONE, SIGNAL_RUN_LAST

if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
    sys.path.insert(0, base_dir)

from extTreeview import ExtTreeView

from tools import consts

# The format of a row in the treeview
(
    ROW_ICO, # Item icon
    ROW_NAME,     # Item name
    ROW_TRK,   # The track object
) = range(3)

# Internal d'n'd (reordering)
DND_REORDERING_ID   = 1024
DND_INTERNAL_TARGET = ('extListview-internal', gtk.TARGET_SAME_WIDGET, DND_REORDERING_ID)

signal_new('tracktreeview-dnd', gtk.TreeView, SIGNAL_RUN_LAST, TYPE_NONE, (gtk.gdk.DragContext, TYPE_INT, TYPE_INT, gtk.SelectionData, TYPE_INT, TYPE_PYOBJECT))



class TrackTreeView(ExtTreeView):
    def __init__(self, colums, use_markup=True):
        ExtTreeView.__init__(self, colums, use_markup)

        #self.set_level_indentation(30)

        # Drag'n'drop management
        self.dndContext    = None
        self.dndSources    = None
        self.dndTargets    = consts.DND_TARGETS.values()
        self.motionEvtId   = None
        self.dndStartPos   = None
        self.dndReordering = False

        self.dndStartPos     = None
        self.isDraggableFunc = lambda: True

        if len(self.dndTargets) != 0:
            # Move one name around while dragging
            # self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, \
            #        self.dndTargets+[DND_INTERNAL_TARGET], gtk.gdk.ACTION_MOVE)
            self.enable_model_drag_dest(self.dndTargets, gtk.gdk.ACTION_DEFAULT)

        self.connect('drag-begin', self.onDragBegin)
        self.connect('drag-motion', self.onDragMotion)
        self.connect('drag-data-received', self.onDragDataReceived)

        #self.connect('button-press-event', self.onButtonPressed)

        self.mark = None
        self.expanded_rows = []
        self.dir_selected = True


    def insert(self, target, source_row, drop_mode=None):
        model = self.store
        if drop_mode == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
            new = model.prepend(target, source_row)
        elif drop_mode == gtk.TREE_VIEW_DROP_INTO_OR_AFTER or drop_mode is None:
            new = model.append(target, source_row)
        elif drop_mode == gtk.TREE_VIEW_DROP_BEFORE:
            new = model.insert_before(None, target, source_row)
        elif drop_mode == gtk.TREE_VIEW_DROP_AFTER:
            new = model.insert_after(None, target, source_row)
        return new

    def appendRow(self, row, parent_iter=None):
        """ Append a row to the tree """
        return self.store.append(parent_iter, row)

    def removeRow(self, iter):
        """ Remove the given row """
        self.store.remove(iter)

    def select_synchronously(self, iter):
        self.get_selection().select_iter(iter)

    def getSelectedRows(self):
        sel_paths = self.selection.get_selected_rows()[1]
        return [self.store.get_iter(path) for path in sel_paths]

    def getFirstSelectedRow(self):
        sel_rows = self.getSelectedRows()
        if sel_rows:
            return sel_rows[0]
        return None

    def iterSelectedRows(self):
        """ Iterate on selected rows """
        for iter in self.getSelectedRows():
            yield iter

    def removeSelectedRows(self):
        '''
        Remove the rows in reverse order.
        Otherwise we remove the wrong rows,
        because the paths will have changed
        '''
        for iter in reversed(self.getSelectedRows()):
            self.removeRow(iter)

    def setItem(self, iter, colIndex, value):
        """ Change the value of the given item """
        self.store.set_value(iter, colIndex, value)

    def getItem(self, iter, colIndex):
        """ Return the value of the given item """
        return self.store.get_value(iter, colIndex)

    def getTrack(self, iter):
        return self.getItem(iter, ROW_TRK)

    def getLabel(self, iter):
        label = self.getItem(iter, ROW_NAME)
        from xml.sax.saxutils import unescape
        label = unescape(label)
        return label

    def setLabel(self, iter, label):
        label = label.replace('_', ' ')
        return self.setItem(iter, ROW_NAME, label)

    def scroll(self, iter):
        self.scroll_to_cell(self.store.get_path(iter))

    def scroll_to_first_selection(self):
        iter = self.getFirstSelectedRow()
        if not iter:
            return
        self.scroll(iter)

    def expand(self, iter):
        self.expand_to_path(self.store.get_path(iter))

    def get_nodename(self, iter):
        if not iter:
            return 'NoneValue'
        return self.store.get_value(iter, 1)

    def get_first_iter(self):
        return self.store.get_iter_root()

    def get_last_iter(self):
        lowest_root = self.get_last_root()
        if lowest_root is None:
            return None
        return self.get_lowest_descendant(lowest_root)

    def get_last_root(self):
        root_nodes = len(self.store)
        if root_nodes == 0:
            return None
        return self.store.iter_nth_child(None, root_nodes-1)

    def get_all_parents(self, iter):
        """Returns a list of parent, grandparent, greatgrandparent, etc."""
        parent = self.store.iter_parent(iter)
        while parent:
            yield parent
            parent = self.store.iter_parent(parent)

    def iter_prev(self, iter):
        """Return the previous iter on the same level."""
        path = self.store.get_path(iter)
        position = path[-1]
        if position == 0:
            return None
        prev_path = list(path)[:-1]
        prev_path.append(position - 1)
        prev = self.store.get_iter(tuple(prev_path))
        return prev

    def get_prev_iter(self, iter=None):
        '''
        Look for the previous iter in the tree
        '''
        if iter is None:
            iter = self.getMark()
            if iter is None:
                return None

        # Check for a sibling or its children
        prev_iter = self.iter_prev(iter)
        if prev_iter:
            return self.get_lowest_descendant(prev_iter)

        # Check for the parent
        parent_iter = self.store.iter_parent(iter)
        if parent_iter:
            return parent_iter
        return None

    def get_next_iter(self, iter=None):
        '''
        Look for the next iter in the tree
        '''
        if iter is None:
            iter = self.getMark()
            if iter is None:
                return self.get_first_iter()

        # Check for a child
        if self.store.iter_has_child(iter):
            first_child = self.store.iter_nth_child(iter, 0)
            return first_child

        # Check for a sibling
        next_iter = self.store.iter_next(iter)
        if next_iter:
            return next_iter

        # iter has no following siblings -> return uncle
        return self.get_next_iter_on_higher_level(iter)

    def get_next_iter_on_higher_level(self, iter):
        """Goes up in the hierarchy until one parent has a next node."""
        while True:
            parent = self.store.iter_parent(iter)
            if parent is None:
                # We have reached the top of the tree
                return None
            uncle = self.store.iter_next(parent)
            if uncle:
                return uncle
            iter = parent

    def get_prev_iter_or_parent(self, iter):
        """
        Returns the previous node on the same level if there is one or the
        parent iter. If "iter" is the first iter, None is returned.
        """
        prev_iter = self.iter_prev(iter)
        if prev_iter:
            return prev_iter
        parent = self.store.iter_parent(iter)
        return parent

    def get_lowest_descendant(self, iter):
        '''
        Find lowest descendant or return iter
        - a    -> c
          - b  -> b
          - c  -> c
        - d    -> d
        '''
        descendant = None
        if self.store.iter_has_child(iter):
            last_child = self.get_last_child_iter(iter)
            descendant = self.get_lowest_descendant(last_child)
        return descendant or iter

    def get_last_child_iter(self, iter):
        ''''''
        if not self.store.iter_has_child(iter):
            return None
        children = self.store.iter_n_children(iter)
        return self.store.iter_nth_child(iter, children-1)

    def get_last_iter_on_same_level(self, iter):
        ''''''
        parent = self.store.iter_parent(iter)
        if parent:
            return self.get_last_child_iter(parent)
        while True:
            sibling = self.store.iter_next(iter)
            if not sibling:
                return iter
            iter = sibling

    def iter_children(self, parent=None):
        """ Iterate on the children of the given iter """
        iter = self.store.iter_children(parent)

        while iter is not None:
            yield iter
            iter = self.store.iter_next(iter)


    # --== Mark management ==--


    def hasMark(self):
        """ True if a mark has been set """
        return self.mark is not None and self.mark.valid()


    def clearMark(self):
        """ Remove the mark """
        self.mark = None


    def getMark(self):
        """ Return the iter of the marked row """
        if self.mark is None or not self.mark.valid():
            return None
        return self.store.get_iter(self.mark.get_path())


    def setMark(self, iter):
        """ Put the mark on the given row, it will move with the row itself (e.g., D'n'D) """
        self.mark = gtk.TreeRowReference(self.store, self.store.get_path(iter))


    def isAtMark(self, iter):
        '''
        Compare the marker path and the path of iter, because the iters alone
        will not predict equality
        '''
        if not self.hasMark():
            return False
        return self.store.get_path(self.getMark()) == self.store.get_path(iter)



    # DRAG AND DROP

    def select(self, iter):
        '''
        Select and highlight an iter
        '''
        gobject.idle_add(self.get_selection().select_iter, iter)


    def move_selected_rows(self, x, y):
        '''
        Method called when dnd happens inside the treeview
        '''
        drop = self.get_dest_row_at_pos(int(x), int(y))
        selection = self.getSelectedRows()

        model = self.store

        if drop:
            dest, drop_mode = drop
            dest = model.get_iter(dest)
        else:
            # Dropped on free space -> append
            dest, drop_mode = self.get_last_root(), gtk.TREE_VIEW_DROP_AFTER

        self.freeze_child_notify()

        # filter selected tracks whose directories have been selected too
        iters = []
        for iter in selection:
            add = True
            for checked_iter in iters:
                if model.is_ancestor(checked_iter, iter):
                    add = False
            if model.is_ancestor(iter, dest):
                # Do not drop ancestors into children
                add = False
            if add:
                iters.append(iter)

        # Move the iters
        for index, iter in enumerate(iters):
            if index > 0:
                drop_mode = gtk.TREE_VIEW_DROP_AFTER

            track = self.getTrack(iter)
            if track:
                row = model[iter]
                dest = self.insert(dest, row, drop_mode)
                self.select(dest)

                # adjust track label to __new__ parent
                parent = self.store.iter_parent(dest)
                parent_label = self.getLabel(parent) if parent else None
                self.setLabel(dest, track.get_label(parent_label))

                # Handle Mark
                if self.isAtMark(iter):
                    self.setMark(dest)
            else:
                dest = self.move_dir(iter, dest, drop_mode)

        for iter in iters:
            model.remove(iter)

        self.thaw_child_notify()

        # We want to allow dropping tracks only when we are sure that no dir is
        # selected. This is needed for dnd from nautilus.
        self.dir_selected = True


    def move_dir(self, dir_iter, target, drop_mode):
        '''
        Recursive Method that moves a dir to target
        '''
        children = self.store[dir_iter].iterchildren()
        dir_row = self.store[dir_iter]
        new_target = self.insert(target, dir_row, drop_mode)
        self.select(new_target)
        for child in children:
            child = child.iter
            track = self.getTrack(child)
            row = self.store[child]
            if track:
                dest = self.insert(new_target, row, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
                # Handle Mark
                if self.isAtMark(child):
                    self.setMark(dest)
            else:
                self.move_dir(child, new_target, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
        return new_target


    def enableDNDReordering(self):
        """ Enable the use of Drag'n'Drop to reorder the list """
        self.dndReordering = True
        self.dndTargets.append(DND_INTERNAL_TARGET)
        self.enable_model_drag_dest(self.dndTargets, gtk.gdk.ACTION_DEFAULT)


    def onDragDataReceived(self, tree, context, x, y, selection, dndId, time):
        """ Some data has been dropped into the list """
        if dndId == DND_REORDERING_ID:
            self.move_selected_rows(x, y)
        else:
            self.emit('tracktreeview-dnd', context, int(x), int(y), selection, dndId, time)


    def onDragBegin(self, tree, context):
        dir_selected = False
        for row in self.getSelectedRows():
            track = self.getTrack(row)
            if not track:
                dir_selected = True
                break
        self.dir_selected = dir_selected
        if dir_selected:
            self.collapse_all()


    def onDragMotion(self, tree, context, x, y, time):
        """
        Allow the following drops:
        - tracks onto and into dir
        - tracks between dirs
        - dir between dirs

        -> Prevent the drops:
        - dir into dir
        - anything into track
        """
        drop = self.get_dest_row_at_pos(int(x), int(y))

        pos_ok = True

        if drop is not None:
            iter = self.store.get_iter(drop[0])
            depth = self.store.iter_depth(iter)
            track = self.getTrack(iter)

            #import tools
            #self.setLabel(self.get_first_iter(), tools.htmlEscape(str(drop[1])))

            drop_into = drop[1] in [gtk.TREE_VIEW_DROP_INTO_OR_AFTER, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE]
            drop_around = not drop_into

            # At least one dir is being dropped
            if self.dir_selected:
                # Dirs can only be dropped at the top level
                if drop_into or ((drop_around) and depth > 0):
                    # do not let the user drop anything here
                    pos_ok = False
            else:
                # Tracks can also be dropped into dirs (but not into tracks)
                if (track and drop_into):# or (drop_into and depth > 0):
                    pos_ok = False

        if pos_ok:
            # Everything ok, enable dnd
            self.enable_model_drag_dest(self.dndTargets, gtk.gdk.ACTION_DEFAULT)
        else:
            # do not let the user drop anything here
            self.enable_model_drag_dest([('invalid-position', 0, -1)], gtk.gdk.ACTION_DEFAULT)


if __name__ == '__main__':
    from gobject import TYPE_INT, TYPE_PYOBJECT

    from tools import icons
    from media import getTracks

    tracks = getTracks(['/home/jendrik/Musik/Clearlake - Amber'])

    columns = (('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf), (gtk.CellRendererText(), TYPE_STRING)], True),
                   (None, [(None, TYPE_INT)],                                                                 False),
                   (None, [(None, TYPE_STRING)],                                                               False),
                   (None, [(None, TYPE_PYOBJECT)], False),
                  )

    tree = TrackTreeView(columns, True)

    track = None



    a = tree.appendRow((icons.nullMenuIcon(), 'a', 1, 'something', track), None)
    b = tree.appendRow((icons.nullMenuIcon(), 'b', 1, 'something', track), a)
    c = tree.appendRow((icons.nullMenuIcon(), 'c', 1, 'something', track), a)
    d = tree.appendRow((icons.nullMenuIcon(), 'd', 1, 'something', track), None)

    for iter in [a, b, c, d]:
        next = tree.get_next_iter(iter)
        print tree.get_nodename(iter), '->', tree.get_nodename(next)

    for iter in [a, b, c, d]:
        uncle = tree.get_next_iter_on_higher_level(iter)
        print 'Uncle(%s) = %s' % (tree.get_nodename(iter), tree.get_nodename(uncle))

    for iter in [a, b, c, d]:
        prev = tree.get_prev_iter(iter)
        print tree.get_nodename(prev), '<-', tree.get_nodename(iter)

    for iter in [a, b, c, d]:
        res = tree.get_last_iter_on_same_level(iter)
        print 'Last Sibling(%s) = %s' % (tree.get_nodename(iter), tree.get_nodename(res))

    for iter in [a, b, c, d]:
        res = tree.get_lowest_descendant(iter)
        print 'Lowest Descendant(%s) = %s' % (tree.get_nodename(iter), tree.get_nodename(res))

    res = tree.get_last_iter()
    print 'Last node: %s' % tree.get_nodename(res)

    res = list(tree.iter_children())
    print 'Children of root:', [tree.getLabel(iter) for iter in res]

    res = list(tree.iter_children(a))
    print 'Children of a:', [tree.getLabel(iter) for iter in res]

    win = gtk.Window()
    win.set_size_request(400,300)
    win.connect('destroy', lambda x: sys.exit())
    win.add(tree)
    tree.expand_all()

    win.show_all()
    gtk.main()
