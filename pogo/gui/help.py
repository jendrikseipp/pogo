# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
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

from gi.repository import Pango

from pogo import tools

PANGO_SCALE_FACTOR = 1.2


class HelpDlg:
    """ Show a help dialog box """

    def __init__(self, title):
        """ Constructor """
        wTree = tools.loadGladeFile('HelpDlg.ui')
        self.dialog = wTree.get_object('dlg-main')
        self.text_buffer = wTree.get_object('txt-help').get_buffer()

        self.dialog.set_title(tools.consts.appName)
        self.text_buffer.create_tag('title', weight=Pango.Weight.BOLD, scale=PANGO_SCALE_FACTOR ** 2)
        self.text_buffer.create_tag('section', weight=Pango.Weight.BOLD, scale=PANGO_SCALE_FACTOR)

        self.nbSections = 0
        self.text_buffer.set_text('')
        self.text_buffer.insert_with_tags_by_name(self.text_buffer.get_end_iter(), title + '\n', 'title')

    def addSection(self, title, content):
        """ Create a new section with the given title and content """
        self.nbSections += 1
        self.text_buffer.insert(self.text_buffer.get_end_iter(), '\n\n')
        self.text_buffer.insert_with_tags_by_name(self.text_buffer.get_end_iter(), '%u. %s' % (self.nbSections, title), 'section')
        self.text_buffer.insert(self.text_buffer.get_end_iter(), '\n\n%s' % content)

    def show(self, parent):
        """ Show the help dialog box """
        self.dialog.set_transient_for(parent)
        self.dialog.show_all()
        self.dialog.run()
        self.dialog.hide()
