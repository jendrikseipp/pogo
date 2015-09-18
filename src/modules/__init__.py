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

import gobject, gtk, gui, gui.preferences, os, sys, threading, traceback

from tools   import consts, log, prefs
from gettext import gettext as _


# Information exported by a module
(
    MODINFO_NAME,           # Name of the module, must be unique
    MODINFO_L10N,           # Name translated into the current locale
    MODINFO_DESC,           # Description of the module, translated into the current locale
    MODINFO_DEPS,           # A list of special Python dependencies (e.g., pynotify)
    MODINFO_MANDATORY,      # True if the module cannot be disabled
    MODINFO_CONFIGURABLE    # True if the module can be configured
) = range(6)


# Values associated with a module
(
    MOD_PMODULE,      # The actual Python module object
    MOD_CLASSNAME,    # The classname of the module
    MOD_INSTANCE,     # Instance, None if not currently enabled
    MOD_INFO          # A tuple exported by the module, see above definition
) = range(4)


class LoadException(Exception):
    """ Raised when a module could not be loaded """

    def __init__(self, errMsg):
        """ Constructor """
        self.errMsg = errMsg

    def __str__(self):
        """ String representation """
        return self.errMsg


def __checkDeps(deps):
    """ Given a list of Python modules, return a list of the modules that are unavailable """
    unmetDeps = []
    for module in deps:
        try:    __import__(module)
        except: unmetDeps.append(module)
    return unmetDeps


def load(name):
    """ Load the given module, may raise LoadException """
    mModulesLock.acquire()
    module = mModules[name]
    mModulesLock.release()

    # Check dependencies
    unmetDeps = __checkDeps(module[MOD_INFO][MODINFO_DEPS])
    if len(unmetDeps) != 0:
        errMsg  = _('The following Python modules are not available:')
        errMsg += '\n     * '
        errMsg += '\n     * '.join(unmetDeps)
        errMsg += '\n\n'
        errMsg += _('You must install them if you want to enable this module.')
        raise LoadException, errMsg

    # Instantiate the module
    try:
        module[MOD_INSTANCE] = getattr(module[MOD_PMODULE], module[MOD_CLASSNAME])()
        module[MOD_INSTANCE].start()

        mHandlersLock.acquire()
        if module[MOD_INSTANCE] in mHandlers[consts.MSG_EVT_MOD_LOADED]:
            module[MOD_INSTANCE].postMsg(consts.MSG_EVT_MOD_LOADED)
        mHandlersLock.release()

        log.logger.info('Module loaded: %s' % module[MOD_CLASSNAME])
        mEnabledModules.append(name)
        prefs.set(__name__, 'enabled_modules', mEnabledModules)
    except:
        raise LoadException, traceback.format_exc()


def unload(name):
    """ Unload the given module """
    mModulesLock.acquire()
    module               = mModules[name]
    instance             = module[MOD_INSTANCE]
    module[MOD_INSTANCE] = None
    mModulesLock.release()

    if instance is not None:
        mHandlersLock.acquire()
        instance.postMsg(consts.MSG_EVT_MOD_UNLOADED)
        for handlers in [handler for handler in mHandlers.itervalues() if instance in handler]:
            handlers.remove(instance)
        mHandlersLock.release()

        mEnabledModules.remove(name)
        log.logger.info('Module unloaded: %s' % module[MOD_CLASSNAME])
        prefs.set(__name__, 'enabled_modules', mEnabledModules)


def getModules():
    """ Return a copy of all known modules """
    mModulesLock.acquire()
    copy = mModules.items()
    mModulesLock.release()
    return copy


def register(module, msgList):
    """ Register the given module for all messages in the given list/tuple """
    mHandlersLock.acquire()
    for msg in msgList:
        mHandlers[msg].add(module)
    mHandlersLock.release()


def showPreferences():
    """ Show the preferences dialog box """
    gobject.idle_add(gui.preferences.show)


def __postMsg(msg, params={}):
    """ This is the 'real' postMsg function, which must be executed in the GTK main loop """
    mHandlersLock.acquire()
    for module in mHandlers[msg]:
        module.postMsg(msg, params)
    mHandlersLock.release()


def postMsg(msg, params={}):
    """ Post a message to the queue of modules that registered for this type of message """
    # We need to ensure that posting messages will be done by the GTK main loop
    # Otherwise, the code of threaded modules could be executed in the caller's thread, which could cause problems when calling GTK functions
    gobject.idle_add(__postMsg, msg, params)


def __postQuitMsg():
    """ This is the 'real' postQuitMsg function, which must be executed in the GTK main loop """
    __postMsg(consts.MSG_EVT_APP_QUIT)
    for modData in mModules.itervalues():
        if modData[MOD_INSTANCE] is not None:
            modData[MOD_INSTANCE].join()
    # Don't exit the application right now, let modules do their job before
    gobject.idle_add(gtk.main_quit)


def postQuitMsg():
    """ Post a MSG_EVT_APP_QUIT in each module's queue and exit the application """
    # As with postMsg(), we need to ensure that the code will be executed by the GTK main loop
    gobject.idle_add(__postQuitMsg)


mMenuItems  = {}
mSeparator  = None
mAccelGroup = None


def __addMenuItem(label, callback, accelerator):
    """ This is the 'real' addMenuItem function, which must be executed in the GTK main loop """
    global mAccelGroup, mSeparator

    menu = prefs.getWidgetsTree().get_object('menu-edit')

    # Remove all menu items
    if len(mMenuItems) != 0:
        menu.remove(mSeparator)
        for menuitem in mMenuItems.itervalues():
            menu.remove(menuitem)

    # Create a new menu item for the module
    menuitem = gtk.MenuItem(label)
    menuitem.connect('activate', callback)
    menuitem.show()
    mMenuItems[label] = menuitem

    # Add an accelerator if needed
    if accelerator is not None:
        if mAccelGroup is None:
            mAccelGroup = gtk.AccelGroup()
            prefs.getWidgetsTree().get_object('win-main').add_accel_group(mAccelGroup)

        key, mod = gtk.accelerator_parse(accelerator)
        menuitem.add_accelerator('activate', mAccelGroup, key, mod, gtk.ACCEL_VISIBLE)

    # Create the separator?
    if mSeparator is None:
        mSeparator = gtk.SeparatorMenuItem()
        mSeparator.show()

    # Re-add items alphabetically, including the new one
    menu.insert(mSeparator, 0)
    for item in sorted(mMenuItems.items(), key = lambda item: item[0], reverse = True):
        menu.insert(item[1], 0)


def addMenuItem(label, callback, accelerator=None):
    """ Add a menu item to the 'modules' menu """
    gobject.idle_add(__addMenuItem, label, callback, accelerator)


def __delMenuItem(label):
    """ This is the 'real' delMenuItem function, which must be executed in the GTK main loop """
    # Make sure the menu item is there
    if label not in mMenuItems:
        return

    menu = prefs.getWidgetsTree().get_object('menu-edit')

    # Remove all current menu items
    menu.remove(mSeparator)
    for menuitem in mMenuItems.itervalues():
        menu.remove(menuitem)

    # Delete the given menu item
    del mMenuItems[label]

    # Re-add items if needed
    if len(mMenuItems) != 0:
        menu.insert(mSeparator, 0)
        for item in sorted(mMenuItems.items(), key = lambda item: item[0], reverse = True):
            menu.insert(item[1], 0)


def delMenuItem(label):
    """ Delete a menu item from the 'modules' menu """
    gobject.idle_add(__delMenuItem, label)


# --== Base classes for modules ==--


class ModuleBase:
    """ This class makes sure that all modules have some mandatory functions """

    def join(self):
        pass

    def start(self):
        pass

    def configure(self, parent):
        pass

    def handleMsg(self, msg, params):
        pass

    def restartRequired(self):
        gobject.idle_add(gui.infoMsgBox, None, _('Restart required'),
            _('You must restart the application for this modification to take effect.'))



class Module(ModuleBase):
    """ This is the base class for non-threaded modules """

    def __init__(self, handlers):
        self.handlers = handlers
        register(self, handlers.keys())

    def postMsg(self, msg, params={}):
        gobject.idle_add(self.__dispatch, msg, params)

    def __dispatch(self, msg, params):
        self.handlers[msg](**params)



class ThreadedModule(threading.Thread, ModuleBase):
    """ This is the base class for threaded modules """

    def __init__(self, handlers):
        """ Constructor """
        import Queue

        # Attributes
        self.queue        = Queue.Queue(0)            # List of queued messages
        self.gtkResult    = None                      # Value returned by the function executed in the GTK loop
        self.gtkSemaphore = threading.Semaphore(0)    # Used to execute some code in the GTK loop

        # Initialization
        threading.Thread.__init__(self)

        # Add QUIT and UNLOADED messages if needed
        # These messages are required to exit the thread's loop
        if consts.MSG_EVT_APP_QUIT not in handlers:     handlers[consts.MSG_EVT_APP_QUIT]     = lambda: None
        if consts.MSG_EVT_MOD_UNLOADED not in handlers: handlers[consts.MSG_EVT_MOD_UNLOADED] = lambda: None

        self.handlers = handlers
        register(self, handlers.keys())

    def __gtkExecute(self, func):
        """ Private function, must be executed in the GTK main loop """
        self.gtkResult = func()
        self.gtkSemaphore.release()

    def gtkExecute(self, func):
        """ Execute func in the GTK main loop, and block the execution of the thread until done """
        gobject.idle_add(self.__gtkExecute, func)
        self.gtkSemaphore.acquire()
        return self.gtkResult

    def threadExecute(self, func, *args):
        """
            Schedule func(*args) to be called by the thread
            This is used to avoid func to be executed in the GTK main loop
        """
        self.postMsg(consts.MSG_CMD_THREAD_EXECUTE, (func, args))

    def postMsg(self, msg, params={}):
        """ Enqueue a message in this threads's message queue """
        self.queue.put((msg, params))

    def run(self):
        """ Wait for messages and handle them """
        msg = None
        while msg != consts.MSG_EVT_APP_QUIT and msg != consts.MSG_EVT_MOD_UNLOADED:
            (msg, params) = self.queue.get(True)

            if msg == consts.MSG_CMD_THREAD_EXECUTE:
                (func, args) = params
                func(*args)
            else:
                self.handlers[msg](**params)


# --== Entry point ==--


mModDir         = os.path.dirname(__file__)                                    # Where modules are located
mModules        = {}                                                           # All known modules associated to an 'active' boolean
mHandlers       = dict([(msg, set()) for msg in xrange(consts.MSG_END_VALUE)]) # For each message, store the set of registered modules
mModulesLock    = threading.Lock()                                             # Protects the modules list from concurrent access
mHandlersLock   = threading.Lock()                                             # Protects the handlers list from concurrent access
mEnabledModules = prefs.get(__name__, 'enabled_modules', [])                   # List of modules currently enabled


# Do not load modules in blacklist. They also won't show up in the preferences
blacklist = ['__init__.py', 'Zeitgeist.py']


def load_enabled_modules():
    # Find modules, instantiate those that are mandatory or that have been previously enabled by the user
    sys.path.append(mModDir)
    for file in sorted(os.path.splitext(file)[0] for file in os.listdir(mModDir)
                       if file.endswith('.py') and file not in blacklist):
        try:
            pModule = __import__(file)
            modInfo = getattr(pModule, 'MOD_INFO')

            # Should it be instanciated?
            instance = None
            if modInfo[MODINFO_MANDATORY] or modInfo[MODINFO_NAME] in mEnabledModules:
                if len(__checkDeps(modInfo[MODINFO_DEPS])) == 0:
                    instance = getattr(pModule, file)()
                    instance.start()
                    log.logger.info('Module loaded: %s' % file)
                else:
                    log.logger.error('Unable to load module %s because of missing dependencies' % file)

            # Add it to the dictionary
            mModules[modInfo[MODINFO_NAME]] = [pModule, file, instance, modInfo]
        except:
            log.logger.error('Unable to load module %s\n\n%s' % (file, traceback.format_exc()))

    # Remove enabled modules that are no longer available
    mEnabledModules[:] = [module for module in mEnabledModules if module in mModules]
    prefs.set(__name__, 'enabled_modules', mEnabledModules)
