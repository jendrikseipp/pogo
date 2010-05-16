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

import cgi, gobject, gtk, gui, modules, tools

from gettext import gettext as _


(
    ROW_ENABLED,    # True if the module is currently enabled
    ROW_TEXT,       # Name and description of the module
    ROW_ICON,       # An icon indicating whether the module is configurable
    ROW_UNLOADABLE, # True if the module can be disabled
    ROW_INSTANCE,   # Instance of the module, if any
    ROW_MODINFO     # Information exported by a module
) = range(6)


class Preferences:
    """ Allow the user to load/unload/configure modules """

    def __init__(self):
        """ Constructor """
        self.window = gui.window.Window('Preferences.glade', 'vbox1', __name__, _('Preferences'), 390, 350)
        # List of modules
        toggleRdr = gtk.CellRendererToggle()
        columns   = (('',   [(toggleRdr, gobject.TYPE_BOOLEAN)],             ROW_ENABLED,    False, True),
                     ('',   [(gtk.CellRendererText(), gobject.TYPE_STRING)], ROW_TEXT,       True,  True),
                     ('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf)],    ROW_ICON,       False, True),
                     (None, [(None, gobject.TYPE_BOOLEAN)],                  ROW_UNLOADABLE, False, False),
                     (None, [(None, gobject.TYPE_PYOBJECT)],                 ROW_INSTANCE,   False, False),
                     (None, [(None, gobject.TYPE_PYOBJECT)],                 ROW_MODINFO,    False, False))

        self.list = gui.extListview.ExtListView(columns, sortable=False, useMarkup=True, canShowHideColumns=False)
        self.list.set_headers_visible(False)
        self.list.addColumnAttribute(0, toggleRdr, 'activatable', ROW_UNLOADABLE)
        toggleRdr.connect('toggled', self.onModuleToggled)
        self.window.getWidget('scrolledwindow1').add(self.list)
        self.fillList()
        # GTK handlers
        self.window.getWidget('btn-help').connect('clicked', self.onHelp)
        self.list.get_selection().connect('changed', self.onSelectionChanged)
        self.window.getWidget('btn-prefs').connect('clicked', self.onPreferences)
        self.window.getWidget('btn-close').connect('clicked', lambda btn: self.window.hide())


    def show(self):
        """ Show the dialog box """
        if not self.window.isVisible():
            self.list.unselectAll()
            self.window.getWidget('btn-close').grab_focus()
            self.window.getWidget('btn-prefs').set_sensitive(False)
        self.window.show()


    def fillList(self):
        """ Fill the list of modules """
        rows = []
        for (name, data) in modules.getModules():
            instance     = data[modules.MOD_INSTANCE]
            mandatory    = data[modules.MOD_INFO][modules.MODINFO_MANDATORY]
            configurable = data[modules.MOD_INFO][modules.MODINFO_CONFIGURABLE]

            if configurable or not mandatory:
                if configurable and instance is not None: icon = tools.consts.icoBtnPrefs
                else:                                     icon = None

                text = '<b>%s</b>\n<small>%s</small>' % (cgi.escape(_(name)), cgi.escape(data[modules.MOD_INFO][modules.MODINFO_DESC]))
                rows.append((instance is not None, text, icon, not mandatory, instance, data[modules.MOD_INFO]))

        rows.sort(key=lambda row: row[ROW_TEXT])
        self.list.replaceContent(rows)


    # --== GTK handlers ==--


    def onModuleToggled(self, renderer, path):
        """ A module has been enabled/disabled """
        row  = self.list.getRow(path)
        name = row[ROW_MODINFO][modules.MODINFO_NAME]

        if row[ROW_ENABLED]:
            modules.unload(name)
        else:
            try:                             modules.load(name)
            except modules.LoadException, e: gui.errorMsgBox(self.window, _('Unable to load this module.'), str(e))

        self.fillList()


    def onHelp(self, btn):
        """ Show a small help message box """
        helpDlg = gui.help.HelpDlg(_('Modules'))
        helpDlg.addSection(_('Description'),
                           _('This dialog box shows the list of available modules, which are small pieces of code that add '
                             'some functionnalities to the application. You can enable/disable a module by checking/unchecking '
                             'the check box in front of it. Note that some modules (e.g., the File Explorer) cannot be disabled.'))
        helpDlg.addSection(_('Configuring a Module'),
                           _('When a module may be configured, a specific icon is displayed on the right of the corresponding line. '
                             'To configure a module, simply select it and then click on the "Preferences" button on the bottom of '
                             'the dialog box. Note that configuring a module is only possible when it is enabled.'))
        helpDlg.show(self.window)


    def onSelectionChanged(self, selection):
        """ Decide whether the new selection may be configured """
        sensitive = self.list.getSelectedRowsCount() == 1 and self.list.getFirstSelectedRow()[ROW_ICON] is not None
        self.window.getWidget('btn-prefs').set_sensitive(sensitive)


    def onPreferences(self, btn):
        """ Configure the selected module """
        self.list.getFirstSelectedRow()[ROW_INSTANCE].configure(self.window)


# --== Global functions ==--


__instance = None

def show():
    """ Show the preferences dialog box """
    global __instance

    if __instance is None:
        __instance = Preferences()
    __instance.show()
