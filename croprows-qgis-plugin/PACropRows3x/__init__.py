# -*- coding: utf-8 -*-
"""PACropRows QGIS plugin
This plugin generates crop rows lines from drone aerial images

    :author: Andres Herrera
    :begin: 2018-02-22
    :updated : 2020-01-12
    :copyright: 2018 - 2020 by Andres Herrera - Universidad del Valle
    :email: fabio.herrera@correounivalle.edu.co

    This program is free software; you can redistribute it and/or modify   it under the terms of the GNU General Public License as published by  the Free Software Foundation; either version 2 of the License, or 
    (at your option) any later version.  This script initializes the plugin, making it known to QGIS.

"""

def __init__(self):
    "croprows file utils module starts"
    print('PACropRows')

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PACropRows class from file PACropRows.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .crop_rows import PACropRows
    return PACropRows(iface)
