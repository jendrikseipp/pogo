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

import gtk, media, modules, os, tools

from tools   import consts, prefs, icons
from media   import playlist
from gettext import gettext as _
from os.path import isdir, isfile
from gobject import idle_add, TYPE_STRING, TYPE_INT

MOD_INFO = ('File Explorer', _('File Explorer'), _('Browse your file system'), [], True, False)
MOD_L10N = MOD_INFO[modules.MODINFO_L10N]

# Default preferences
PREFS_DEFAULT_MEDIA_FOLDERS     = {_('Home'): consts.dirBaseUsr, _('Root'): '/'}    # List of media folders that are used as roots for the file explorer
PREFS_DEFAULT_ADD_BY_FILENAME   = False                                             # True if files should be added to the playlist by their filename
PREFS_DEFAULT_SHOW_HIDDEN_FILES = False                                             # True if hidden files should be shown


# The format of a row in the treeview
(
    ROW_PIXBUF,    # Item icon
    ROW_NAME,      # Item name
    ROW_TYPE,      # The type of the item (e.g., directory, file)
    ROW_FULLPATH   # The full path to the item
) = range(4)


# The possible types for a node of the tree
(
    TYPE_DIR,   # A directory
    TYPE_FILE,  # A media file
    TYPE_NONE   # A fake item, used to display a '+' in front of a directory when needed
) = range(3)


class FileExplorer(modules.Module):
    """ This explorer lets the user browse the disk from a given root directory (e.g., ~/, /) """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_APP_QUIT:         self.onAppQuit,
                        consts.MSG_EVT_APP_STARTED:      self.onAppStarted,
                        #consts.MSG_EVT_EXPLORER_CHANGED: self.onExplorerChanged,
                   }

        modules.Module.__init__(self, handlers)


    def createTree(self):
        """ Create the tree used to display the file system """
        from gui import extTreeview

        columns = (('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf), (gtk.CellRendererText(), TYPE_STRING)], True),
                   (None, [(None, TYPE_INT)],                                                                  False),
                   (None, [(None, TYPE_STRING)],                                                               False))

        self.tree = extTreeview.ExtTreeView(columns, True)

        self.scrolled.add(self.tree)
        self.tree.setDNDSources([consts.DND_TARGETS[consts.DND_POGO_URI]])
        self.tree.connect('drag-data-get', self.onDragDataGet)
        self.tree.connect('key-press-event', self.onKeyPressed)
        self.tree.connect('exttreeview-button-pressed', self.onMouseButton)
        self.tree.connect('exttreeview-row-collapsed', self.onRowCollapsed)
        self.tree.connect('exttreeview-row-expanded', self.onRowExpanded)


    def getTreeDump(self, path=None):
        """ Recursively dump the given tree starting at path (None for the root of the tree) """
        list = []

        for child in self.tree.iterChildren(path):
            row = self.tree.getRow(child)

            if self.tree.getNbChildren(child) == 0: grandChildren = None
            elif self.tree.row_expanded(child):     grandChildren = self.getTreeDump(child)
            else:                                   grandChildren = []

            list.append([(row[ROW_NAME], row[ROW_TYPE], row[ROW_FULLPATH]), grandChildren])

        return list


    def restoreTreeDump(self, dump, parent=None):
        """ Recursively restore the dump under the given parent (None for the root of the tree) """
        for item in dump:
            (name, type, path) = item[0]

            if type == TYPE_FILE:
                self.tree.appendRow((icons.mediaFileMenuIcon(), name, TYPE_FILE, path), parent)
            else:
                newNode = self.tree.appendRow((icons.dirMenuIcon(), name, TYPE_DIR, path), parent)

                if item[1] is not None:
                    fakeChild = self.tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), newNode)

                    if len(item[1]) != 0:
                        # We must expand the row before adding the real children, but this works only if there is already at least one child
                        self.tree.expandRow(newNode)
                        self.restoreTreeDump(item[1], newNode)
                        self.tree.removeRow(fakeChild)


    def saveTreeState(self):
        """ Return a dictionary representing the current state of the tree """
        if self.currRoot is not None:
            self.treeState[self.currRoot] = {
                        'tree-state':     self.getTreeDump(),
                        'selected-paths': self.tree.getSelectedPaths(),
                        'vscrollbar-pos': self.scrolled.get_vscrollbar().get_value(),
                        'hscrollbar-pos': self.scrolled.get_hscrollbar().get_value(),
                   }


    def sortKey(self, row):
        """ Key function used to compare two rows of the tree """
        return row[ROW_NAME].lower()


    def setShowHiddenFiles(self, showHiddenFiles):
        """ Show/hide hidden files """
        if showHiddenFiles != self.showHiddenFiles:
            # Update the configuration window if needed
            if self.cfgWin is not None and self.cfgWin.isVisible():
                self.cfgWin.getWidget('chk-hidden').set_active(showHiddenFiles)

            self.showHiddenFiles = showHiddenFiles
            self.refresh()


    def play(self, replace, path=None):
        """
            Replace/extend the tracklist
            If 'path' is None, use the current selection
        """
        ## never replace
        replace = False
        
        if path is None: tracks = media.getTracks([row[ROW_FULLPATH] for row in self.tree.getSelectedRows()], self.addByFilename)
        else:            tracks = media.getTracks([self.tree.getRow(path)[ROW_FULLPATH]], self.addByFilename)

        if replace: modules.postMsg(consts.MSG_CMD_TRACKLIST_SET, {'tracks': tracks, 'playNow': True})
        else:       modules.postMsg(consts.MSG_CMD_TRACKLIST_ADD, {'tracks': tracks, 'playNow': False})


    def renameFolder(self, oldName, newName):
        """ Rename a folder """
        self.folders[newName] = self.folders[oldName]
        del self.folders[oldName]

        if oldName in self.treeState:
            self.treeState[newName] = self.treeState[oldName]
            del self.treeState[oldName]

        modules.postMsg(consts.MSG_CMD_EXPLORER_RENAME, {'modName': MOD_L10N, 'expName': oldName, 'newExpName': newName})


    # --== Tree management ==--


    def startLoading(self, row):
        """ Tell the user that the contents of row is being loaded """
        name = self.tree.getItem(row, ROW_NAME)
        self.tree.setItem(row, ROW_NAME, '%s  <span size="smaller" foreground="#909090">%s</span>' % (name, _('loading...')))


    def stopLoading(self, row):
        """ Tell the user that the contents of row has been loaded"""
        name  = self.tree.getItem(row, ROW_NAME)
        index = name.find('<')

        if index != -1:
            self.tree.setItem(row, ROW_NAME, name[:index-2])


    def getDirContents(self, directory):
        """ Return a tuple of sorted rows (directories, playlists, mediaFiles) for the given directory """
        playlists   = []
        mediaFiles  = []
        directories = []

        for (file, path) in tools.listDir(directory, self.showHiddenFiles):
            if isdir(path):
                directories.append((icons.dirMenuIcon(), tools.htmlEscape(unicode(file, errors='replace')), TYPE_DIR, path))
            elif isfile(path):
                if media.isSupported(file):
                    mediaFiles.append((icons.mediaFileMenuIcon(), tools.htmlEscape(unicode(file, errors='replace')), TYPE_FILE, path))
                elif playlist.isSupported(file):
                    playlists.append((icons.mediaFileMenuIcon(), tools.htmlEscape(unicode(file, errors='replace')), TYPE_FILE, path))

        playlists.sort(key=self.sortKey)
        mediaFiles.sort(key=self.sortKey)
        directories.sort(key=self.sortKey)

        return (directories, playlists, mediaFiles)


    def exploreDir(self, parent, directory, fakeChild=None):
        """
            List the contents of the given directory and append it to the tree as a child of parent
            If fakeChild is not None, remove it when the real contents has been loaded
        """
        directories, playlists, mediaFiles = self.getDirContents(directory)

        self.tree.appendRows(directories, parent)
        self.tree.appendRows(playlists,   parent)
        self.tree.appendRows(mediaFiles,  parent)

        if fakeChild is not None:
            self.tree.removeRow(fakeChild)

        idle_add(self.updateDirNodes(parent).next)


    def updateDirNodes(self, parent):
        """ This generator updates the directory nodes, based on whether they should be expandable """
        for child in self.tree.iterChildren(parent):
            # Only directories need to be updated and since they all come first, we can stop as soon as we find something else
            if self.tree.getItem(child, ROW_TYPE) != TYPE_DIR:
                break

            # Make sure it's readable
            directory  = self.tree.getItem(child, ROW_FULLPATH)
            hasContent = False
            if os.access(directory, os.R_OK | os.X_OK):
                for (file, path) in tools.listDir(directory, self.showHiddenFiles):
                    if isdir(path) or (isfile(path) and (media.isSupported(file) or playlist.isSupported(file))):
                        hasContent = True
                        break

            # Append/remove children if needed
            if hasContent and self.tree.getNbChildren(child) == 0:      self.tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), child)
            elif not hasContent and self.tree.getNbChildren(child) > 0: self.tree.removeAllChildren(child)

            yield True

        if parent is not None:
            self.stopLoading(parent)

        yield False


    def refresh(self, treePath=None):
        """ Refresh the tree, starting from treePath """
        if treePath is None: directory = self.folders[self.currRoot]
        else:                directory = self.tree.getItem(treePath, ROW_FULLPATH)

        directories, playlists, mediaFiles = self.getDirContents(directory)

        disk                   = directories + playlists + mediaFiles
        diskIndex              = 0
        childIndex             = 0
        childLeftIntentionally = False

        while diskIndex < len(disk):
            rowPath = self.tree.getChild(treePath, childIndex)

            # Did we reach the end of the tree?
            if rowPath is None:
                break

            file      = disk[diskIndex]
            cmpResult = cmp(self.sortKey(self.tree.getRow(rowPath)), self.sortKey(file))

            if cmpResult < 0:
                # We can't remove the only child left, to prevent the node from being closed automatically
                if self.tree.getNbChildren(treePath) == 1:
                    childLeftIntentionally = True
                    break

                self.tree.removeRow(rowPath)
            else:
                if cmpResult > 0:
                    self.tree.insertRowBefore(file, treePath, rowPath)
                diskIndex  += 1
                childIndex += 1

        # If there are tree rows left, all the corresponding files are no longer there
        if not childLeftIntentionally:
            while childIndex < self.tree.getNbChildren(treePath):
                self.tree.removeRow(self.tree.getChild(treePath, childIndex))

        # Disk files left?
        while diskIndex < len(disk):
            self.tree.appendRow(disk[diskIndex], treePath)
            diskIndex += 1

        # Deprecated child left? (must be done after the addition of left disk files)
        if childLeftIntentionally:
            self.tree.removeRow(self.tree.getChild(treePath, 0))

        # Update nodes' appearance
        if len(directories) != 0:
            idle_add(self.updateDirNodes(treePath).next)

        # Recursively refresh expanded rows
        for child in self.tree.iterChildren(treePath):
            if self.tree.row_expanded(child):
                idle_add(self.refresh, child)


    # --== GTK handlers ==--


    def onMouseButton(self, tree, event, path):
        """ A mouse button has been pressed """
        if event.button == 3:
            self.onShowPopupMenu(tree, event.button, event.time, path)
        elif path is not None:
            if event.button == 2:
                self.play(False, path)
            elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                if   tree.getItem(path, ROW_PIXBUF) != icons.dirMenuIcon(): self.play(True)
                elif tree.row_expanded(path):                               tree.collapse_row(path)
                else:                                                       tree.expand_row(path, False)


    def onShowPopupMenu(self, tree, button, time, path):
        """ Show a popup menu """
        popup = gtk.Menu()

        # Play selection
        play = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
        play.set_label(_('Append'))
        popup.append(play)

        if path is None:
            play.set_sensitive(False)
        else:
            play.connect('activate', lambda widget: self.play(True))

        popup.append(gtk.SeparatorMenuItem())

        # Collapse all nodes
        ##collapse = gtk.ImageMenuItem(_('Collapse all'))
        ##collapse.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
        ##collapse.connect('activate', lambda widget: tree.collapse_all())
        ##popup.append(collapse)

        # Refresh the view
        refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        refresh.connect('activate', lambda widget: self.refresh())
        popup.append(refresh)

        ##popup.append(gtk.SeparatorMenuItem())

        # Show hidden files
        ##hidden = gtk.CheckMenuItem(_('Show hidden files'))
        ##hidden.set_active(self.showHiddenFiles)
        ##hidden.connect('toggled', lambda item: self.setShowHiddenFiles(item.get_active()))
        ##popup.append(hidden)

        popup.show_all()
        popup.popup(None, None, None, button, time)


    def onKeyPressed(self, tree, event):
        """ A key has been pressed """
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'F5':       self.refresh()
        elif keyname == 'plus':   tree.expandRows()
        elif keyname == 'Left':   tree.collapseRows()
        elif keyname == 'Right':  tree.expandRows()
        elif keyname == 'minus':  tree.collapseRows()
        elif keyname == 'space':  tree.switchRows()
        elif keyname == 'Return': self.play(True)


    def onRowExpanded(self, tree, path):
        """ Replace the fake child by the real children """
        self.startLoading(path)
        idle_add(self.exploreDir, path, tree.getItem(path, ROW_FULLPATH), tree.getChild(path, 0))


    def onRowCollapsed(self, tree, path):
        """ Replace all children by a fake child """
        tree.removeAllChildren(path)
        tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), path)


    def onDragDataGet(self, tree, context, selection, info, time):
        """ Provide information about the data being dragged """
        import urllib
        selection.set('text/uri-list', 8, ' '.join([urllib.pathname2url(file) for file in [row[ROW_FULLPATH] for row in tree.getSelectedRows()]]))
        
        
    def add_dir(self, path):
        name = tools.dirname(path)
        name = tools.htmlEscape(unicode(name, errors='replace'))
        parent = self.tree.appendRow((icons.dirMenuIcon(), name, TYPE_DIR, path), None)
        self.exploreDir(parent, path)
        
        
    def populate_tree(self):
        '''
        Bookmarks code from Quod Libet
        '''
        if self.tree is None:
            self.createTree()
            
        folders = ['/', consts.dirBaseUsr]
        
        def add_path(path, prepend=False):
            if not os.path.isdir(path) or path in folders:
                return
            if prepend:
                folders.insert(0, path)
            else:
                folders.append(path)
                
        
        import urlparse, urllib2
        
        # Read XDG music directory
        xdg_file = os.path.join(consts.dirBaseUsr, '.config', 'user-dirs.dirs')
        if os.path.exists(xdg_file):
            with open(xdg_file) as f:
                import re
                folder_regex = re.compile(r'XDG_MUSIC_DIR\=\"\$HOME/(.+)\"')
                
                content = f.read()
                match = folder_regex.search(content)
                if False and match:
                    dirname = match.group(1)
                    path = os.path.join(consts.dirBaseUsr, dirname)
                    folders.append(None)
                    add_path(path, prepend=False)
                else:
                    # Try other music folders
                    names = ['Music', 'Albums', _('Music'), _('Albums')]
                    for name in names:
                        for case in [name, name.lower()]:
                            music_folder = os.path.join(consts.dirBaseUsr, name)
                            if os.path.isdir(music_folder):
                                add_path(music_folder)
                
        
        # Read in the GTK bookmarks list; gjc says this is the right way
        #bookmarks_file = os.path.join(consts.dirBaseUsr, ".gtk-bookmarks")
        #if os.path.exists(bookmarks_file):
        #    try:
        #        with open(bookmarks_file) as f:
        #            folders.append(None)
        #            for line in f.readlines():
        #                folder_url = line.split()[0]
        #                path = urlparse.urlsplit(folder_url)[2]
        #                # "My%20folder" -> "My folder"
        #                path = urllib2.unquote(path)
        #                add_path(path)
        #    except EnvironmentError:
        #        pass

        #def is_folder(filename):
        #    return filename is None or os.path.isdir(filename)
        #folders = filter(is_folder, folders)
        #if folders[-1] is None:
        #    folders.pop()
        
        self.tree.set_row_separator_func(lambda model, iter: model[iter][ROW_NAME] is None)
        
        for path in folders:
            if path is None:
                # Separator
                self.tree.appendRow((icons.nullMenuIcon(), None, TYPE_NONE, None), None)
            else:
                self.add_dir(path)


   # --== Message handlers ==--


    def onAppStarted(self):
        """ The module has been loaded """
        self.tree            = None
        self.cfgWin          = None
        self.folders         = prefs.get(__name__, 'media-folders', PREFS_DEFAULT_MEDIA_FOLDERS)
        self.scrolled        = gtk.ScrolledWindow()
        self.currRoot        = None
        self.treeState       = prefs.get(__name__, 'saved-states', {})
        self.addByFilename   = prefs.get(__name__, 'add-by-filename',  PREFS_DEFAULT_ADD_BY_FILENAME)
        self.showHiddenFiles = prefs.get(__name__, 'show-hidden-files', PREFS_DEFAULT_SHOW_HIDDEN_FILES)

        self.scrolled.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled.show()

        #for name in self.folders:
        #    modules.postMsg(consts.MSG_CMD_EXPLORER_ADD, {'modName': MOD_L10N, 'expName': name, 'icon': icons.dirMenuIcon(), 'widget': self.scrolled})
        
        ##
        combo = prefs.getWidgetsTree().get_widget('combo-explorer')
        combo.hide()
        self.notebook = prefs.getWidgetsTree().get_widget('notebook-explorer')
        self.notebook.append_page(self.scrolled)
        self.notebook.set_current_page(1)
        self.populate_tree()


    def onAppQuit(self):
        """ The module is going to be unloaded """
        self.saveTreeState()
        prefs.set(__name__, 'saved-states',      self.treeState)
        prefs.set(__name__, 'media-folders',     self.folders)
        prefs.set(__name__, 'add-by-filename',   self.addByFilename)
        prefs.set(__name__, 'show-hidden-files', self.showHiddenFiles)


    def onExplorerChanged(self, modName, expName):
        """ A new explorer has been selected """
        if modName == MOD_L10N and self.currRoot != expName:
            # Create the tree if needed
            if self.tree is None:
                self.createTree()

            # Save the state of the current root
            if self.currRoot is not None:
                self.saveTreeState()
                self.tree.clear()

            self.currRoot = expName

            # Restore the state of the new root
            if expName in self.treeState:
                self.tree.handler_block_by_func(self.onRowExpanded)
                self.restoreTreeDump(self.treeState[expName]['tree-state'])
                self.tree.handler_unblock_by_func(self.onRowExpanded)

                idle_add(self.scrolled.get_vscrollbar().set_value, self.treeState[expName]['vscrollbar-pos'])
                idle_add(self.scrolled.get_hscrollbar().set_value, self.treeState[expName]['hscrollbar-pos'])
                idle_add(self.tree.selectPaths, self.treeState[expName]['selected-paths'])
                idle_add(self.refresh)
            else:
                self.exploreDir(None, self.folders[self.currRoot])
                if len(self.tree) != 0:
                    self.tree.scroll_to_cell(0)


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration dialog """
        if self.cfgWin is None:
            from gui import extListview, window

            self.cfgWin = window.Window('FileExplorer.glade', 'vbox1', __name__, MOD_L10N, 370, 400)
            # Create the list of folders
            txtRdr  = gtk.CellRendererText()
            pixRdr  = gtk.CellRendererPixbuf()
            columns = ((None, [(txtRdr, TYPE_STRING)],                           0, False, False),
                       ('',   [(pixRdr, gtk.gdk.Pixbuf), (txtRdr, TYPE_STRING)], 2, False, True))

            self.cfgList = extListview.ExtListView(columns, sortable=False, useMarkup=True, canShowHideColumns=False)
            self.cfgList.set_headers_visible(False)
            self.cfgWin.getWidget('scrolledwindow1').add(self.cfgList)
            # Connect handlers
            self.cfgList.connect('key-press-event', self.onCfgKeyPressed)
            self.cfgList.get_selection().connect('changed', self.onCfgSelectionChanged)
            self.cfgWin.getWidget('btn-add').connect('clicked', self.onAddFolder)
            self.cfgWin.getWidget('btn-remove').connect('clicked', lambda btn: self.onRemoveSelectedFolder(self.cfgList))
            self.cfgWin.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWin.getWidget('btn-rename').connect('clicked', self.onRenameFolder)
            self.cfgWin.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWin.hide())
            self.cfgWin.getWidget('btn-help').connect('clicked', self.onHelp)

        if not self.cfgWin.isVisible():
            self.populateFolderList()
            self.cfgWin.getWidget('chk-hidden').set_active(self.showHiddenFiles)
            self.cfgWin.getWidget('chk-add-by-filename').set_active(self.addByFilename)
            self.cfgWin.getWidget('btn-ok').grab_focus()

        self.cfgWin.show()


    def populateFolderList(self):
        """ Populate the list of known folders """
        self.cfgList.replaceContent([(name, icons.dirBtnIcon(), '<b>%s</b>\n<small>%s</small>' % (tools.htmlEscape(name), tools.htmlEscape(path)))
                                     for name, path in sorted(self.folders.iteritems())])


    def onAddFolder(self, btn):
        """ Let the user add a new folder to the list """
        from gui import selectPath

        result = selectPath.SelectPath(MOD_L10N, self.cfgWin, self.folders.keys()).run()

        if result is not None:
            name, path = result
            self.folders[name] = path
            self.populateFolderList()
            modules.postMsg(consts.MSG_CMD_EXPLORER_ADD, {'modName': MOD_L10N, 'expName': name, 'icon': icons.dirMenuIcon(), 'widget': self.scrolled})


    def onRemoveSelectedFolder(self, list):
        """ Remove the selected media folder """
        import gui

        if list.getSelectedRowsCount() == 1:
            remark   = _('You will be able to add this root folder again later on if you wish so.')
            question = _('Remove the selected entry?')
        else:
            remark   = _('You will be able to add these root folders again later on if you wish so.')
            question = _('Remove all selected entries?')

        if gui.questionMsgBox(self.cfgWin, question, '%s %s' % (_('Your media files will not be deleted.'), remark)) == gtk.RESPONSE_YES:
            for row in self.cfgList.getSelectedRows():
                name = row[0]
                modules.postMsg(consts.MSG_CMD_EXPLORER_REMOVE, {'modName': MOD_L10N, 'expName': name})
                del self.folders[name]

                # Remove the tree, if any, from the scrolled window
                if self.currRoot == name:
                    self.currRoot = None

                # Remove the saved state of the tree, if any
                if name in self.treeState:
                    del self.treeState[name]

            self.cfgList.removeSelectedRows()


    def onRenameFolder(self, btn):
        """ Let the user rename a folder """
        from gui import selectPath

        name         = self.cfgList.getSelectedRows()[0][0]
        forbidden    = [rootName for rootName in self.folders if rootName != name]
        pathSelector = selectPath.SelectPath(MOD_L10N, self.cfgWin, forbidden)

        pathSelector.setPathSelectionEnabled(False)
        result = pathSelector.run(name, self.folders[name])

        if result is not None and result[0] != name:
            self.renameFolder(name, result[0])
            self.populateFolderList()


    def onCfgKeyPressed(self, list, event):
        """ Remove the selection if possible """
        if gtk.gdk.keyval_name(event.keyval) == 'Delete':
            self.onRemoveSelectedFolder(list)


    def onCfgSelectionChanged(self, selection):
        """ The selection has changed """
        self.cfgWin.getWidget('btn-remove').set_sensitive(selection.count_selected_rows() != 0)
        self.cfgWin.getWidget('btn-rename').set_sensitive(selection.count_selected_rows() == 1)


    def onBtnOk(self, btn):
        """ The user has clicked on the OK button """
        self.cfgWin.hide()
        self.setShowHiddenFiles(self.cfgWin.getWidget('chk-hidden').get_active())
        self.addByFilename = self.cfgWin.getWidget('chk-add-by-filename').get_active()


    def onHelp(self, btn):
        """ Display a small help message box """
        import gui

        helpDlg = gui.help.HelpDlg(MOD_L10N)
        helpDlg.addSection(_('Description'),
                           _('This module allows you to browse the files on your drives.'))
        helpDlg.addSection(_('Usage'),
                           _('At least one root folder must be added to browse your files. This folder then becomes the root of the '
                             'file explorer tree in the main window.'))
        helpDlg.show(self.cfgWin)
