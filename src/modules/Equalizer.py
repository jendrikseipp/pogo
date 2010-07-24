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

import gobject, gtk, gui, modules

from tools   import consts, prefs
from gettext import gettext as _

MOD_INFO = ('Equalizer', _('Equalizer'), _('Tune the level of the frequency bands'), [], False, True)


# Entries of the presets combo box
(
    ROW_PRESET_IS_SEPARATOR,
    ROW_PRESET_NAME,
    ROW_PRESET_VALUES,
) = range(3)


class Equalizer(modules.Module):
    """ This module lets the user tune the level of 10 frequency bands """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_MOD_LOADED:   self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:  self.onAppStarted,
                        consts.MSG_EVT_MOD_UNLOADED: self.onModUnloaded,
                   }

        modules.Module.__init__(self, handlers)


    def modInit(self):
        """ Initialize the module """
        self.lvls      = prefs.get(__name__, 'levels', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.preset    = prefs.get(__name__, 'preset', _('Flat'))
        self.cfgWindow = None

        modules.addMenuItem(_('Equalizer'), self.configure, '<Control>E')


    # --== Message handlers ==--


    def onModLoaded(self):
        """ The module has been loaded """
        self.modInit()
        self.restartRequired()


    def onModUnloaded(self):
        """ The module has been unloaded """
        modules.delMenuItem(_('Equalizer'))
        self.restartRequired()


    def onAppStarted(self):
        """ The application has started """
        self.modInit()
        modules.postMsg(consts.MSG_CMD_ENABLE_EQZ)
        modules.postMsg(consts.MSG_CMD_SET_EQZ_LVLS, {'lvls': self.lvls})


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration dialog """
        if self.cfgWindow is None:
            import gui.window

            self.cfgWindow = gui.window.Window('Equalizer.glade', 'vbox1', __name__, MOD_INFO[modules.MODINFO_L10N], 580, 300)

            self.timer      = None
            self.combo      = self.cfgWindow.getWidget('combo-presets')
            self.scales     = []
            self.comboStore = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
            self.targetLvls = []

            # Setup the scales
            for i in xrange(10):
                self.scales.append(self.cfgWindow.getWidget('vscale' + str(i)))
                self.scales[i].set_value(self.lvls[i])
                self.scales[i].connect('value-changed', self.onScaleValueChanged, i)

            # Setup the combo box
            txtRenderer = gtk.CellRendererText()
            self.combo.pack_start(txtRenderer, True)
            self.combo.add_attribute(txtRenderer, 'text', ROW_PRESET_NAME)
            self.combo.set_model(self.comboStore)
            self.combo.set_row_separator_func(lambda model, iter: model.get_value(iter, ROW_PRESET_IS_SEPARATOR))

            # Add presets to the combo box
            self.comboStore.append((False, 'Classic V', ( 7,  5,  0,  -5,  -8,  -7,  -4,  -1,   3,   5)))
            self.comboStore.append((False, 'Classical', ( 0,  0,  0,   0,   0,   0,   0,  -2,  -5,  -6)))
            self.comboStore.append((False, 'Dance'    , ( 6,  5,  4,   3,   1,   0,  -3,  -5,  -5,   0)))
            self.comboStore.append((False, 'Flat'     , ( 0,  0,  0,   0,   0,   0,   0,   0,   0,   0)))
            self.comboStore.append((False, 'Live'     , (-4, -2,  0,   2,   3,   3,   3,   3,   2,   0)))
            self.comboStore.append((False, 'Metal'    , ( 3,  4,  5,   1,  -2,   0,   1,   1,  -1,  -1)))
            self.comboStore.append((False, 'Pop'      , ( 3,  6,  3,  -2,  -4,  -3,   0,   2,   3,   5)))
            self.comboStore.append((False, 'Reggae'   , ( 1,  1,  1,   0,  -3,   0,   3,   4,   2,   1)))
            self.comboStore.append((False, 'Rock'     , ( 5,  4,  2,  -2,  -3,  -3,   2,   4,   5,   5)))
            self.comboStore.append((False, 'Techno'   , ( 4,  4,  3,   2,   0,  -4,  -2,   0,   3,   4)))

            # Select the right entry
            if self.preset is None:
                self.comboStore.insert(0, (False, _('Custom'), None))
                self.comboStore.insert(1, (True,  '',          None))
                self.combo.set_active(0)
            else:
                for i, preset in enumerate(self.comboStore):
                    if preset[ROW_PRESET_NAME] == self.preset:
                        self.combo.set_active(i)
                        break

            # Events
            self.cfgWindow.getWidget('btn-save').connect('clicked',  self.onBtnSave)
            self.cfgWindow.getWidget('btn-open').connect('clicked',  self.onBtnOpen)
            self.cfgWindow.getWidget('btn-close').connect('clicked', lambda btn: self.cfgWindow.hide())
            self.combo.connect('changed', self.onPresetChanged)

        if not self.cfgWindow.isVisible():
            self.cfgWindow.getWidget('btn-close').grab_focus()

        self.cfgWindow.show()


    def onPresetChanged(self, combo):
        """ A preset has been selected """
        idx = combo.get_active()
        if idx != -1:
            iter = self.comboStore.get_iter(idx)
            preset = self.comboStore.get_value(iter, ROW_PRESET_NAME)
            self.jumpToTargetLvls(self.comboStore.get_value(iter, ROW_PRESET_VALUES))

            # Remove the 'Custom' entry if needed
            if self.preset is None:
                self.comboStore.remove(self.comboStore.get_iter((0, )))
                self.comboStore.remove(self.comboStore.get_iter((0, )))

            self.preset = preset
            prefs.set(__name__, 'preset', self.preset)



    def onBtnSave(self, btn):
        """ Save the current levels to a file"""
        outFile = gui.fileChooser.save(self.cfgWindow, _('Save levels'), 'levels.dat')

        if outFile is not None:
            output = open(outFile, 'wt')
            for i in xrange(10):
                output.write(str(self.lvls[i]) + '\n')
            output.close()


    def onBtnOpen(self, btn):
        """ Load the levels from a file"""
        inFile = gui.fileChooser.openFile(self.cfgWindow, _('Load levels'))

        if inFile is not None:
            input = open(inFile, 'rt')
            lines = input.readlines()
            input.close()

            lvls      = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            isInvalid = True

            if len(lines) == 10:
                isInvalid = False
                for i in xrange(10):
                    elts = lines[i].split()

                    try:
                        if len(elts) == 1:
                            lvls[i] = float(elts[0])
                            if lvls[i] >= -24 and lvls[i] <= 12:
                                continue
                    except:
                        pass

                    isInvalid = True
                    break

            if isInvalid:
                gui.errorMsgBox(self.cfgWindow, _('Could not load the file'), _('The format of the file is incorrect.'))
            else:
                self.jumpToTargetLvls(lvls)

                # Add a 'custom' entry to the presets if needed
                if self.preset is not None:
                    self.preset = None
                    prefs.set(__name__, 'preset', self.preset)
                    self.combo.handler_block_by_func(self.onPresetChanged)
                    self.comboStore.insert(0, (False, _('Custom'), None))
                    self.comboStore.insert(1, (True,  '',          None))
                    self.combo.set_active(0)
                    self.combo.handler_unblock_by_func(self.onPresetChanged)


    def onScaleValueChanged(self, scale, idx):
        """ The user has moved one of the scales """
        # Add a 'custom' entry to the presets if needed
        if self.preset is not None:
            self.preset = None
            prefs.set(__name__, 'preset', self.preset)
            self.combo.handler_block_by_func(self.onPresetChanged)
            self.comboStore.insert(0, (False, _('Custom'), None))
            self.comboStore.insert(1, (True,  '',          None))
            self.combo.set_active(0)
            self.combo.handler_unblock_by_func(self.onPresetChanged)

        self.lvls[idx] = scale.get_value()
        prefs.set(__name__, 'levels', self.lvls)
        modules.postMsg(consts.MSG_CMD_SET_EQZ_LVLS, {'lvls': self.lvls})


    def jumpToTargetLvls(self, targetLvls):
        """ Move the scales until they reach some target levels """
        if self.timer is not None:
            gobject.source_remove(self.timer)

        self.timer      = gobject.timeout_add(20, self.timerFunc)
        self.targetLvls = targetLvls

        for i in xrange(10):
            self.scales[i].handler_block_by_func(self.onScaleValueChanged)


    def timerFunc(self):
        """ Move a bit the scales to their target value """
        isFinished = True

        # Move the scales a bit
        for i in xrange(10):
            currLvl    = self.scales[i].get_value()
            targetLvl  = self.targetLvls[i]
            difference = targetLvl - currLvl

            if abs(difference) <= 0.25:
                newLvl = targetLvl
            else:
                newLvl     = currLvl + (difference / 8.0)
                isFinished = False

            self.lvls[i] = newLvl
            self.scales[i].set_value(newLvl)

        # Set the equalizer to the new levels
        modules.postMsg(consts.MSG_CMD_SET_EQZ_LVLS, {'lvls': self.lvls})

        if isFinished:
            self.timer = None
            prefs.set(__name__, 'levels', self.lvls)

            # Make sure labels are up to date (sometimes they aren't when we're done with the animation)
            # Also unblock the handlers
            for i in xrange(10):
                self.scales[i].queue_draw()
                self.scales[i].handler_unblock_by_func(self.onScaleValueChanged)

            return False

        return True
