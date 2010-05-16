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

import gobject, gui, modules

from tools   import consts, prefs
from gettext import gettext as _

MOD_INFO    = ('Equalizer', _('Equalizer'), _('Tune the level of the frequency bands'), [], False, True)
MOD_L10N    = MOD_INFO[modules.MODINFO_L10N]
MOD_NAME    = MOD_INFO[modules.MODINFO_NAME]
ZERO_LEVELS = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


class Equalizer(modules.Module):
    """ This module lets the user tune the level of 10 frequency bands """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_APP_STARTED, consts.MSG_EVT_MOD_LOADED, consts.MSG_EVT_MOD_UNLOADED))


    def onModLoaded(self):
        """ The module has been loaded """
        self.lvls      = prefs.get(__name__, 'levels', ZERO_LEVELS)
        self.cfgWindow = None


    def onAppStarted(self):
        """ The module has been loaded """
        self.onModLoaded()
        modules.postMsg(consts.MSG_CMD_ENABLE_EQZ)
        modules.postMsg(consts.MSG_CMD_SET_EQZ_LVLS, {'lvls': self.lvls})


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_APP_STARTED:
            self.onAppStarted()
        elif msg == consts.MSG_EVT_MOD_LOADED:
            self.onModLoaded()
            gui.infoMsgBox(None, _('Restart required'), _('You must restart the application for this modification to take effect.'))
        elif msg == consts.MSG_EVT_MOD_UNLOADED:
            gui.infoMsgBox(None, _('Restart required'), _('You must restart the application for this modification to take effect.'))


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration dialog """
        if self.cfgWindow is None:
            self.timer      = None
            self.scales     = []
            self.handlers   = []
            self.cfgWindow  = gui.window.Window('Equalizer.glade', 'vbox1', __name__, MOD_L10N, 675, 415)
            self.targetLvls = []

            for i in xrange(10):
                self.scales.append(self.cfgWindow.getWidget('vscale' + str(i)))
                self.scales[i].set_value(self.lvls[i])
                self.handlers.append(self.scales[i].connect('value-changed', self.onScaleValueChanged, i))

            self.cfgWindow.getWidget('btn-save').connect('clicked',   self.onBtnSave)
            self.cfgWindow.getWidget('btn-open').connect('clicked',   self.onBtnOpen)
            self.cfgWindow.getWidget('btn-close').connect('clicked',  lambda btn: self.cfgWindow.hide())
            self.cfgWindow.getWidget('btn-center').connect('clicked', lambda btn: self.jumpToTargetLvls(ZERO_LEVELS))

        if not self.cfgWindow.isVisible():
            self.cfgWindow.getWidget('btn-close').grab_focus()

        self.cfgWindow.show()


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

            if isInvalid: gui.errorMsgBox(self.cfgWindow, _('Could not load the file'), _('The format of the file is incorrect.'))
            else:         self.jumpToTargetLvls(lvls)


    def onScaleValueChanged(self, scale, idx):
        """ The user has adjusted one of the scales """
        self.lvls[idx] = scale.get_value()
        prefs.set(__name__, 'levels', self.lvls)
        modules.postMsg(consts.MSG_CMD_SET_EQZ_LVLS, {'lvls': self.lvls})


    def jumpToTargetLvls(self, targetLvls):
        """ Move the scales until they reach some target levels """
        if self.timer is not None:
            gobject.source_remove(self.timer)

        self.timer      = gobject.timeout_add(20, self.timerFunc)
        self.targetLvls = targetLvls


    def timerFunc(self):
        """ Move a bit the scales to their target value """
        isFinished = True

        # Disconnect handlers before moving the scales
        for i in xrange(10):
            self.scales[i].disconnect(self.handlers[i])

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

        # Reconnect the handlers
        for i in xrange(10):
            self.handlers[i] = self.scales[i].connect('value-changed', self.onScaleValueChanged, i)

        # Set the equalizer to the new levels
        prefs.set(__name__, 'levels', self.lvls)
        modules.postMsg(consts.MSG_CMD_SET_EQZ_LVLS, {'lvls': self.lvls})

        return not isFinished
