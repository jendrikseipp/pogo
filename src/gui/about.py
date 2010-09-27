# -*- coding: utf-8 -*-
#
# Authors: Ingelrest François (Francois.Ingelrest@gmail.com)
#          Jendrik Seipp (jendrikseipp@web.de)
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

import gtk, os.path, webbrowser

from tools   import consts
from gettext import gettext as _


def show(parent):
    """ Show an about dialog box """
    dlg = gtk.AboutDialog()
    dlg.set_transient_for(parent)

    # Hook to handle clicks on the URL
    gtk.about_dialog_set_url_hook(lambda dlg, url: webbrowser.open(url))

    # Set credit information
    dlg.set_name(consts.appName)
    dlg.set_comments('...Simples!')
    dlg.set_version(consts.appVersion)
    dlg.set_website(consts.urlMain)
    dlg.set_website_label(consts.urlMain)
    dlg.set_translator_credits(_('translator-credits'))
    #dlg.set_artists([])

    dlg.set_authors([
        _('Developer:'),
        'Jendrik Seipp <jendrikseipp@web.de>',
        
        '',
        _('Thanks to:'),
        'François Ingelrest <Francois.Ingelrest@gmail.com>',
        _('(Developer of Decibel Audio Player)')
    ])

    # Set logo
    dlg.set_logo(gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon128))

    # Load the licence from the disk if possible
    if os.path.isfile(consts.fileLicense):
        dlg.set_license(open(consts.fileLicense).read())
        dlg.set_wrap_license(True)

    dlg.run()
    dlg.destroy()
