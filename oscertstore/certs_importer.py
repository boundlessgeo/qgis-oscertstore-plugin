# -*- coding: utf-8 -*-
"""
***************************************************************************
    certs_importer.py
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

import wincertstore
from qgis.core import QgsApplication, QgsAuthCertUtils
from qgis.PyQt.QtCore import QByteArray
from qgis.PyQt.QtNetwork import QSslCertificate


# noinspection PyArgumentList
def run(plugin):
    """Import intermediate certs and return True on success"""

    if QgsApplication.authManager().isDisabled():
        plugin.log(QgsApplication.authManager().disabledMessage())
        return False

    ca_pems = dict()
    with wincertstore.CertSystemStore("CA") as store:
        for cert in store.itercerts(usage=None):
            # plugin.log(cert.get_name())
            # plugin.log(cert.enhanced_keyusage_names())
            ca_pems[cert.get_name()] = cert.get_pem()

    plugin.log(plugin.tr("Number of possible CAs found: {0}").format(
        len(ca_pems)))

    if not ca_pems:
        return False

    ca_certs = []
    trusted_cas = QgsApplication.authManager().trustedCaCertsCache()

    for ca_cn, ca_pem in ca_pems.items():
        try:
            ca_bytes = ca_pem.encode('ASCII')
        except UnicodeEncodeError:
            continue
        pem_ba = QByteArray(ca_bytes)
        cas = QSslCertificate.fromData(pem_ba)
        # plugin.log("Converted PEM to QSslCertificate {0}: ".format(ca_cn))
        if not cas:
            plugin.log(
                plugin.tr(
                    "Could not convert PEM to QSslCertificate: {0}").format(
                    ca_cn
                )
            )
            continue

        ca = cas[0]
        # noinspection PyArgumentList
        if not QgsAuthCertUtils.certIsViable(cert=ca):
            plugin.log(plugin.tr("  cert not viable: {0}").format(ca_cn))
            continue
        # noinspection PyArgumentList
        if not QgsAuthCertUtils.certificateIsAuthority(cert=ca):
            plugin.log(plugin.tr("  cert not a CA: {0}").format(ca_cn))
            continue
        if ca in trusted_cas:
            plugin.log(
                plugin.tr("  cert already in trusted CA cache: {0}").format(
                    ca_cn)
            )
            continue
        plugin.log(plugin.tr("  found CA to add: {0}").format(ca_cn))
        ca_certs.append(ca)

    if ca_certs:
        plugin.log(plugin.tr("Storing CAs in auth system db"))
        if not QgsApplication.authManager().storeCertAuthorities(ca_certs):
            plugin.log(plugin.tr("  FAILED"))
            return False
        plugin.log(plugin.tr("  SUCCESS"))
        plugin.log(plugin.tr("Reinitializing auth system SSL caches"))
        QgsApplication.authManager().initSslCaches()
        return True
    else:
        plugin.log(plugin.tr("No CAs found to store in auth system db"))
    return True
