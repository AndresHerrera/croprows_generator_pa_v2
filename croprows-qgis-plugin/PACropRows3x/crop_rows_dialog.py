# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PACropRowsDialog
                                 A QGIS plugin
 This plugin generates crop rows lines from drone aerial images
                             -------------------
        begin                : 2018-02-22
        updated              : 2020-01-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 - 2020 by Andres Herrera - Universidad del Valle
        email                : fabio.herrera@correounivalle.edu.co
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

"""PACropRowsDialog 

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""

#import os
#from PyQt5 import QtGui, uic

import os
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'crop_rows_dialog_base.ui'))
    
#FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'crop_rows_dialog_base.ui'))

#class PACropRowsDialog(QtGui.QDialog, FORM_CLASS):
class PACropRowsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PACropRowsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #self.setupUi(self)
        self.setupUi(self)
        self.plugin_dir = os.path.dirname(__file__)
