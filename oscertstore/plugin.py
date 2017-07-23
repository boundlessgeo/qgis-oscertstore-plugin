# -*- coding: utf-8 -*-

"""
***************************************************************************
    __init__.py
    ---------------------
    Date                 : July 2017
    Copyright            : (C) 2017 Boundless, http://boundlessgeo.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alessandro Pasotti'
__date__ = 'July 2017'
__copyright__ = '(C) 2017 Boundless, http://boundlessgeo.com'

# This will get replaced with a git SHA1 when you do a git archive

import os
import webbrowser
from sys import platform

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsApplication, QgsMessageLog

from qgiscommons.settings import readSettings, pluginSetting, setPluginSetting
from qgiscommons.gui import addAboutMenu, removeAboutMenu


# This plugin will normaly only run on Windows, the flag
# allows the GUI (but not certs import of course) to work
# on Linux for development and testing purposes
TEST_ON_LINUX=False

class OsCertificateStore:

    def __init__(self, iface):
        self.iface = iface
        self.action_setting = None
        self.action_run = None
        if not self.is_supported():
            return
        
        try:
            from .tests import testerplugin
            from qgistester.tests import addTestModule
            addTestModule(testerplugin, "OS Certificate Store")
        except:
            pass

        readSettings()
        
        # Run on startup
        if pluginSetting('import_enabled'):
            self.run_triggered()


    def log(self, msg, level=QgsMessageLog.INFO):
        QgsMessageLog.logMessage(msg, "OS Certificate Store", level=level)


    def is_supported(self):
        """Check wether this plugin can run in this platform"""
        if platform == "linux" or platform == "linux2":
            # linux
            return False or TEST_ON_LINUX
        elif platform == "darwin":
            # OS X
            return False
        elif platform == "win32":
            # Windows...
            return True
        else:
            return False

    def initGui(self):
        if not self.is_supported():
            return

        icon_setting = QIcon(os.path.dirname(__file__) + "/icons/desktop.svg")

        self.action_setting = QAction(icon_setting, "Import Windows intermediate certificate authorities on startup", self.iface.mainWindow())
        self.action_setting.setObjectName("enableoscertstore")
        self.action_setting.setCheckable(True)
        self.action_setting.setChecked(pluginSetting('import_enabled'))
        self.action_setting.changed.connect(self.setting_changed)
        self.iface.addPluginToMenu("OS Certificate Store", self.action_setting)

        icon_run = QIcon(os.path.dirname(__file__) + "/icons/desktop.svg")
        if pluginSetting('import_successfully_run') or TEST_ON_LINUX:
            self.action_run = QAction(icon_run, "Reimport Windows intermediate certificate authorities", self.iface.mainWindow())
            self.action_run.setObjectName("enableoscertstore")
            self.action_run.triggered.connect(self.run_triggered)
            self.iface.addPluginToMenu("OS Certificate Store", self.action_run)

        # No toolbar and other menus
        #self.iface.addToolBarIcon(self.action)

        #addSettingsMenu("OS Certificate Store")
        #addHelpMenu("OS Certificate Store")
        addAboutMenu("OS Certificate Store")

    def unload(self):
        if not self.is_supported():
            return
        try:
            from .tests import testerplugin
            from qgistester.tests import removeTestModule
            removeTestModule(testerplugin, "OS Certificate Store")
        except:
            pass

        try:
            from lessons import removeLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            removeLessonsFolder(folder)
        except:
            pass

        self.iface.removePluginWebMenu("OS Certificate Store", self.action)
        self.iface.removeToolBarIcon(self.action)
        #removeSettingsMenu("OS Certificate Store")
        removeAboutMenu("OS Certificate Store")
        # removeHelpMenu("OS Certificate Store")

    def setting_changed(self):
        if not self.is_supported():
            return
        self.log("Changed to %s" % self.action_setting.isChecked())
        setPluginSetting('import_enabled', self.action_setting.isChecked())


    def run_triggered(self):
        self.log("Importing intermediate certificates ...")
        try:
            from certs_importer import run
            setPluginSetting('import_successfully_run', run(self))
        except Exception as ex:
            self.log("Error importing certificates: %s" % ex)
            setPluginSetting('import_successfully_run', False)

