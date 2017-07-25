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

import ConfigParser
import os
from functools import partial
from sys import platform

from qgis.core import QgsApplication, QgsMessageLog, QgsMessageOutput
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

try:
    from qgis.core import QgsSettings
except ImportError:
    from qgis.PyQt.QtCore import QSettings as QgsSettings


SETTINGS_KEY = "Boundless/Plugins/OSCertStore"

# This plugin will normaly only run on Windows, the flag
# allows the GUI (but not certs import of course) to work
# on Linux for development and testing purposes
TEST_ON_LINUX = QgsSettings().value(SETTINGS_KEY + '/test_on_linux', False, type=bool)

class OsCertificateStore:

    def __init__(self, iface):
        self.iface = iface
        self.action_setting = None
        self.action_about = None
        self.action_run = None
        if not self.is_supported():
            return
        
        try:
            from .tests import testerplugin
            from qgistester.tests import addTestModule
            addTestModule(testerplugin, "OS Certificate Store")
        except:
            pass


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

        self.action_setting = QAction(self.tr("Import Windows intermediate certificate authorities on startup"), self.iface.mainWindow())
        self.action_setting.setObjectName("enableoscertstore")
        self.action_setting.setCheckable(True)
        self.action_setting.setChecked(QgsSettings().value(SETTINGS_KEY + '/import_enabled', True, type=bool))
        self.action_setting.changed.connect(self.setting_changed)
        self.iface.addPluginToMenu(self.tr("OS Certificate Store"), self.action_setting)

        icon_run = QIcon(os.path.dirname(__file__) + "/icons/desktop.svg")
        if QgsSettings().value(SETTINGS_KEY + '/import_successfully_run', True, type=bool) or TEST_ON_LINUX:
            self.action_run = QAction(icon_run, self.tr("Reimport Windows intermediate certificate authorities"), self.iface.mainWindow())
            self.action_run.setObjectName("enableoscertstore")
            self.action_run.triggered.connect(partial(self.run_triggered, True))
            self.iface.addPluginToMenu(self.tr("OS Certificate Store"), self.action_run)

        self.action_about = QAction(
        QgsApplication.getThemeIcon('/mActionHelpContents.svg'),
            "About...",
            self.iface.mainWindow())
        self.action_about.setObjectName("oscertstoreabout")
        self.action_about.triggered.connect(self.about_triggered)
        self.iface.addPluginToMenu(self.tr("OS Certificate Store"), self.action_about)

        # No toolbar and other menus
        #self.iface.addToolBarIcon(self.action)
                
        # Run on startup
        if QgsSettings().value(SETTINGS_KEY + '/import_enabled', True, type=bool):
            self.run_triggered(False)


    def unload(self):
        if not self.is_supported():
            return
        try:
            from .tests import testerplugin
            from qgistester.tests import removeTestModule
            removeTestModule(testerplugin, self.tr("OS Certificate Store"))
        except:
            pass

        try:
            from lessons import removeLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            removeLessonsFolder(folder)
        except:
            pass

        self.iface.removePluginMenu(self.tr("OS Certificate Store"), self.action_about)
        self.iface.removePluginMenu(self.tr("OS Certificate Store"), self.action_setting)
        if self.action_run is not None:
            self.iface.removePluginMenu(self.tr("OS Certificate Store"), self.action_run)


    def setting_changed(self):
        if not self.is_supported():
            return
        self.log("Changed to %s" % self.action_setting.isChecked())
        QgsSettings().setValue(SETTINGS_KEY + '/import_enabled', self.action_setting.isChecked())


    def run_triggered(self, notify):
        self.log("Importing intermediate certificates ...")
        try:
            from certs_importer import run
            QgsSettings().setValue(SETTINGS_KEY + '/import_successfully_run', run(self))
            if notify:
                self.iface.messageBar().pushMessage(self.tr("Success"), self.tr("Intermediate certificates imported correctly (see logs for details)."), level=QgsMessageBar.INFO)
        except Exception as ex:
            self.log("Error importing intermediate certificates: %s" % ex)
            QgsSettings().setValue(SETTINGS_KEY + '/import_successfully_run', False)
            if notify:
                self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("There was an error importing intermediate certificates (see the logs for details)."), level=QgsMessageBar.CRITICAL)



    def about_triggered(self):
        dlg = QgsMessageOutput.createMessageOutput()
        dlg.setTitle(self.tr("Plugin info"))
        dlg.setMessage(self._pluginDetails("oscertstore"), QgsMessageOutput.MessageHtml)
        dlg.showMessage()


    def tr(self, msg):
        return msg

    def _pluginDetails(self, namespace):
        config = DictParser()
        config.readfp(open(os.path.join(os.path.realpath(os.path.dirname(__file__)), 'metadata.txt')))
        plugin = config.as_dict()['general']

        html = '<style>body, table {padding:0px; margin:0px; font-family:verdana; font-size: 1.1em;}</style>'
        html += '<body>'
        html += '<table cellspacing="4" width="100%"><tr><td>'
        html += '<h1>{}</h1>'.format(plugin.get('name'))
        html += '<h3>{}</h3>'.format(plugin.get('description'))

        if plugin.get('about'):
            html += plugin.get('about').replace('\n', '<br/>')

        html += '<br/><br/>'

        if plugin.get('category'):
            html += '{}: {} <br/>'.format(self.tr('Category'), plugin.get('category'))

        if plugin.get('tags'):
            html += '{}: {} <br/>'.format(self.tr('Tags'), plugin.get('tags'))

        if plugin.get('homepage') or plugin.get('tracker') or plugin.get('code_repository'):
            html += self.tr('More info:')

            if plugin.get('homepage'):
                html += '<a href="{}">{}</a> &nbsp;'.format(plugin.get('homepage'), self.tr('homepage') )

            if plugin.get('tracker'):
                html += '<a href="{}">{}</a> &nbsp;'.format(plugin.get('tracker'), self.tr('bug_tracker') )

            if plugin.get('code_repository'):
                html += '<a href="{}">{}</a> &nbsp;'.format(plugin.get('code_repository'), self.tr('code_repository') )

            html += '<br/>'

        html += '<br/>'

        if plugin.get('author_email'):
            html += '{}: <a href="mailto:{}">{}</a>'.format(self.tr('Author email'), plugin.get('author_email'), plugin.get('author_name'))
            html += '<br/><br/>'
        elif plugin.get('author'):
            html += '{}: {}'.format(self.tr('Author'), plugin.get('author'))
            html += '<br/><br/>'

        if plugin.get('version_installed'):
            ver = plugin.get('version_installed')
            if ver == '-1':
                ver = '?'

            html += self.tr('Installed version: {} (in {})<br/>'.format(ver, plugin.get('library')))

        if plugin.get('version_available'):
            html += self.tr('Available version: {} (in {})<br/>'.format(plugin.get('version_available'), plugin.get('zip_repository')))

        if plugin.get('changelog'):
            html += '<br/>'
            changelog = self.tr('Changelog:<br/>{} <br/>'.format(plugin.get('changelog')))
            html += changelog.replace('\n', '<br/>')

        html += '</td></tr></table>'
        html += '</body>'

        return html

class DictParser(ConfigParser.ConfigParser):

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d
