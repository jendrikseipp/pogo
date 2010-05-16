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

import pango, tools

mDlg       = None
mTxtBuffer = None


class HelpDlg:
    """ Show a help dialog box """

    def __init__(self, title):
        """ Constructor """
        global mDlg, mTxtBuffer

        if mDlg is None:
            wTree      = tools.loadGladeFile('HelpDlg.glade')
            mDlg       = wTree.get_widget('dlg-main')
            mTxtBuffer = wTree.get_widget('txt-help').get_buffer()

            mDlg.set_title(tools.consts.appName)
            mTxtBuffer.create_tag('title',   weight=pango.WEIGHT_BOLD, scale=pango.SCALE_X_LARGE, justification=pango.ALIGN_RIGHT)
            mTxtBuffer.create_tag('section', weight=pango.WEIGHT_BOLD, scale=pango.SCALE_LARGE)

        self.nbSections = 0
        mTxtBuffer.set_text('')
        mTxtBuffer.insert_with_tags_by_name(mTxtBuffer.get_end_iter(), title + '\n', 'title')


    def addSection(self, title, content):
        """ Create a new section with the given title and content """
        self.nbSections += 1
        mTxtBuffer.insert(mTxtBuffer.get_end_iter(), '\n\n')
        mTxtBuffer.insert_with_tags_by_name(mTxtBuffer.get_end_iter(), '%u. %s' % (self.nbSections, title), 'section')
        mTxtBuffer.insert(mTxtBuffer.get_end_iter(), '\n\n%s' % content)


    def show(self, parent):
        """ Show the help dialog box """
        mDlg.set_transient_for(parent)
        mDlg.show_all()
        mDlg.run()
        mDlg.hide()
