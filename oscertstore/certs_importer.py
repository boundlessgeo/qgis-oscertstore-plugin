# -*- coding: utf-8 -*-
"""
***************************************************************************
    certs_importer.py
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

__author__ = 'Larry Shaffer'
__date__ = 'July 2017'
__copyright__ = '(C) 2017 Boundless, http://boundlessgeo.com'

import wincertstore
from qgis.core import QgsAuthCertUtils, QgsAuthManager
from qgis.PyQt.QtCore import QByteArray
from qgis.PyQt.QtNetwork import QSslCertificate


def run(logger):
    """Import intermediate certs and return True on success"""
    
    if QgsAuthManager.instance().isDisabled():
        logger.log(QgsAuthManager.instance().disabledMessage())
        return False

    ca_pems = dict()
    with wincertstore.CertSystemStore("CA") as store:
        for cert in store.itercerts(usage=None):
            # logger.log(cert.get_name())
            # logger.log(cert.enhanced_keyusage_names())
            ca_pems[cert.get_name()] = cert.get_pem().decode("ascii")

    logger.log("Number of possible CAs found: {0}".format(len(ca_pems)))

    if not ca_pems:
        return False

    ca_certs = []
    trusted_cas = QgsAuthManager.instance().getTrustedCaCertsCache()

    for ca_cn, ca_pem in ca_pems.items():
        pem_ba = QByteArray(ca_pem)
        cas = QSslCertificate.fromData(pem_ba)
        #logger.log("Converted PEM to QSslCertificate {0}: ".format(ca_cn))
        if not cas:
            logger.log("Could not convert PEM to QSslCertificate: {0}".format(ca_cn))
            continue

        ca = cas[0]
        if not ca.isValid():
            logger.log("  cert not valid: {0}".format(ca_cn))
            continue
        if not QgsAuthCertUtils.certificateIsAuthority(ca):
            logger.log("  cert not a CA: {0}".format(ca_cn))
            continue
        if ca in trusted_cas:
            logger.log("  cert already in trusted CA cache: {0}".format(ca_cn))
            continue
        logger.log("  found CA to add: {0}".format(ca_cn))
        ca_certs.append(ca)

    if ca_certs:
        logger.log("Storing CAs in auth system db")
        if not QgsAuthManager.instance().storeCertAuthorities(ca_certs):
            logger.log("  FAILED")
            return False
        logger.log("  SUCCESS")
        logger.log("Reinitializing auth system SSL caches")
        QgsAuthManager.instance().initSslCaches()
        return True
    else:
        logger.log("No CAs found to store in auth system db")
    return False

