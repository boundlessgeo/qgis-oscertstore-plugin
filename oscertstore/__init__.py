# -*- coding: utf-8 -*-
"""
***************************************************************************
    __init__.py
    ---------------------
    Date                 : July 2017, October 2019
    Copyright            : (C) 2017 Boundless, http://boundlessgeo.com
                         : (C) 2019 Planet Inc, https://planet.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
__author__ = 'Planet Federal'
__date__ = 'August 2019'
__copyright__ = '(C) 2019 Planet Inc, https://planet.com'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


import os
import site

site.addsitedir(os.path.abspath(os.path.dirname(__file__) + '/extlibs'))


# noinspection PyPep8Naming
def classFactory(iface):
    from .plugin import OsCertificateStore
    return OsCertificateStore(iface)
