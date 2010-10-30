# -*- coding: utf-8 -*-
#
# Authors: Jendrik Seipp (jendrikseipp@web.de)
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

import os
import subprocess
import logging
import re
from gettext import gettext as _

import gtk
import gobject

import tools
import modules
import media
from tools import consts, prefs
from tools.log import logger


# Module information
MOD_INFO = ('Search', ('Search'), ('Search your filesystem for music'), [], True, False)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]

MIN_CHARS = 3



class Search(modules.ThreadedModule):

    def __init__(self):
        """ Constructor """
        handlers = {
                        #consts.MSG_EVT_MOD_LOADED:         self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:         self.onAppStarted,
                        consts.MSG_EVT_SEARCH_START:        self.onSearch,
                        consts.MSG_EVT_MUSIC_PATHS_CHANGED: self.onPathsChanged,
                   }

        modules.ThreadedModule.__init__(self, handlers)
        
        
    def search_dir(self, dir, query):
        cmd = ['find', dir]
        for part in query.split():
            cmd.extend(['-iwholename', '*%s*' % part])
        logging.info('Searching with command: %s' % ' '.join(cmd))
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
        output = sorted(output.splitlines(), key=lambda path: path.lower())
        logging.info('Results for %s: %s' % (query, len(output)))
        return output
        
        
    def filter_results(self, results, search_path, regexes):
        '''
        Remove subpaths of parent directories
        '''
        def same_case_bold(match):
            return '<b>%s</b>' % match.group(0)
            
        def get_name(path):
            # Remove the search path from the name
            name = path.replace(search_path, '')
            name = name.strip('/')
            name = tools.htmlEscape(name)
            for regex in regexes:
                name = regex.sub(same_case_bold, name)
            return name
        
        dirs = []
        files = []
        for path in results:
            # Check if this is only a subpath of a directory already handled
            is_subpath = False
            for dir in dirs:
                if path.startswith(dir):
                    is_subpath = True
                    break
                    
            if not is_subpath:
                name = get_name(path)
                    
                if os.path.isdir(path):
                    dirs.append((path, name))
                elif media.isSupported(path):
                    files.append((path, name))
        
        return (dirs, files)
        
        
    def cache(self):
        ''' Cache results for a faster first search '''
        for index, path in enumerate(self.paths, 1):
            # Cache dirs one by one after a small timeout 
            gobject.timeout_add_seconds(5 * index, self.search_dir, path, \
                                        'caching_files')


    # --== Message handlers ==--


    def onAppStarted(self):
        """ The module has been loaded """
        wTree = tools.prefs.getWidgetsTree()
        self.searchbox = gtk.Entry()
        self.searchbox.set_size_request(210, -1)
        
        search_container = gtk.HBox()
        search_container.pack_start(self.searchbox, False)
        search_container.show_all()
        
        hbox3 = wTree.get_widget('hbox3')
        hbox3.pack_start(search_container)
        hbox3.set_property('homogeneous', True)
        hbox3.reorder_child(search_container, 0)
        
        
        if hasattr(self.searchbox, 'set_icon_from_stock'):
            #self.searchbox.set_icon_from_stock(0, gtk.STOCK_FIND)
            #self.searchbox.set_icon_sensitive(0, False)
            self.searchbox.set_icon_from_stock(1, gtk.STOCK_CLEAR)
            self.searchbox.connect('icon-press', self.on_searchbox_clear)
        
        self.searchbox.connect('activate', self.on_searchbox_activate)
        self.searchbox.connect('changed', self.on_searchbox_changed)
        
        self.paths = []
        
        
    def onSearch(self, query):
        regexes = [re.compile(part, re.IGNORECASE) for part in query.split()]
        
        all_dirs = []
        all_files = []
        
        for dir in self.paths:
            results = self.search_dir(dir, query)
            dirs, files = self.filter_results(results, dir, regexes)
            all_dirs.extend(dirs)
            all_files.extend(files)
        modules.postMsg(consts.MSG_EVT_SEARCH_END, 
                            {'results': (all_dirs, all_files), 'query': query})
        
    
    def onPathsChanged(self, paths):
        self.paths = paths
        self.cache()
        
        
    #------- GTK handlers ----------------
        
    def on_searchbox_activate(self, entry):
        query = self.searchbox.get_text().strip()
        if len(query) < MIN_CHARS:
            msg = 'Search term has to have at least %d characters' % MIN_CHARS
            logging.info(msg)
            return
        #print repr(self.searchbox.get_text()), repr(self.searchbox.get_text().decode('utf-8'))
        query = self.searchbox.get_text().decode('utf-8')
        logging.info('Query: %s' % repr(query))
        modules.postMsg(consts.MSG_EVT_SEARCH_START, {'query': query})
        
        
    def on_searchbox_changed(self, entry):
        if self.searchbox.get_text().strip() == '':
            modules.postMsg(consts.MSG_EVT_SEARCH_RESET, {})
            
    
    def on_searchbox_clear(self, entry, icon_pos, event):
        '''
        An icon has been pressed
        '''
        if icon_pos == 1:
            self.searchbox.set_text('')
