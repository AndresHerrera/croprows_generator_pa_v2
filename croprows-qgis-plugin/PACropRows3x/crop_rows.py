# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PACropRows
                                 A QGIS plugin
 This plugin generates crop rows lines from drone aerial images for sugracane fields
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
from __future__ import print_function
import io
import os
import os.path
import shutil
import random
import time
import subprocess

from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,qVersion,QUrl
from qgis.PyQt.QtGui import QIcon,QValidator
from PyQt5.QtGui import  QDoubleValidator
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QFileDialog, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar, QProgressDialog
from qgis._core import Qgis, QgsMapLayer, QgsRasterLayer, QgsVectorLayer, QgsProject,QgsMessageLog,QgsWkbTypes,QgsCoordinateReferenceSystem
from qgis.utils import reloadPlugin
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
import xml.etree.ElementTree as cET
import xml.etree.cElementTree as ET
#import urlparse
import urllib
import urllib.error
from urllib.request import urlopen,urlretrieve
from urllib.parse import urljoin


    
#import urllib2
import socket
#from qgis.core import QgsMapLayer, QgsMapLayerRegistry
#from qgis.gui import QgsMapLayerComboBox, QgsMapLayerProxyModel, QgsFieldComboBox
# Initialize Qt resources from file resources.py
from .resources import *
#import resourcespat
# Import the code for the dialog
from .crop_rows_dialog import PACropRowsDialog
from functools import partial

import sys
if sys.executable.endswith("pythonw.exe"):
    sys.stdout = sys.stdout = None

""" Croprows projectfile structure
<?xml version="1.0"?>
<croprows>
    <filename name="testimage1.tif" mask="field_boundary.shp">
    	<image_dimensions>17992,23231</image_dimensions>
    	<image_origin>358624,376856</image_origin>
    	<pixel_size>0.0184399,-0.0184401</pixel_size>
    	<image_extents>358624.4387608282850124,376427.6166225711349398,358956.2094862160738558,376855.9995228421757929</image_extents>
    	<epsg>32618</epsg>
    	<projwtk>PROJCS["WGS 84 / UTM zone 18N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-75],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],AUTHORITY["EPSG","32618"],AXIS["Easting",EAST],AXIS["Northing",NORTH]]</projwtk>
    	<seed>4</seed>
        <prj>testimage</prj>
    </filename>
</croprows>
"""

class PACropRows:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        nowTime = time.strftime("%c")
        ## date and time representation
        QgsMessageLog.logMessage('========================================================')
        QgsMessageLog.logMessage('Crop Rows Plugin Starts '+time.strftime('%c'))
        QgsMessageLog.logMessage('========================================================')

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PACropRows_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Crop Rows Generator v1.0')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PACropRows')
        self.toolbar.setObjectName(u'PACropRows')
        self.flagClipTaskDone = 0

        #True only copy files
        #False clip by mask
        self.flagNoCropRaster = False
        
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        
        QgsMessageLog.logMessage('Crop Rows Generator v1.0 - Loaded')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PACropRows', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = PACropRowsDialog()
        icon_path = ':/plugins/PACropRows/icon.png'

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        #self.dlg.textEdit.clear()

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/PACropRows/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Crop Rows UI'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        #self.run_2()
        #self.dlg.textEdit.clear()
        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Crop Rows Generator v1.0'),
                action)
            self.iface.removeToolBarIcon(action)
        #self.dlg.textEdit.clear()
        # remove the toolbar
        del self.toolbar

    def isNotEmpty(s):
        """String is not empty."""
        return bool(s and s.strip())
    
    def url_ok(self,url,timeout=5):
        try:
            #return urllib2.urlopen(url,timeout=timeout).getcode() == 200
            return urllib.request.urlopen(url,timeout=timeout).getcode() == 200
        #except urllib2.URLError as e:
        except urllib.error.URLError as e:
            return False
        except socket.timeout as e:
            QgsMessageLog.logMessage('Socket time out !')
            #print(False)
    
    def readConfigFileFromXML(self):
        """Read config file."""
        #TODO: STDOUT        
        #self.dlg.textEdit.clear()
        #sys.stdout = Log(self.dlg.textEdit)
        #self.dlg.textEdit.clear()
        #self.dlg.textEdit.selectAll()
        #self.dlg.textEdit.setText('')
        self.flagClipTaskDone=0
        
        QgsMessageLog.logMessage('Crop Rows - Plugin Path: '+(os.path.dirname(os.path.abspath(__file__))))
        QgsMessageLog.logMessage('===========================================')
        QgsMessageLog.logMessage('Reading configuration file')

        xmlConfigFile = os.path.join((os.path.dirname(os.path.abspath(__file__))), 'config.xml' )

        QgsMessageLog.logMessage('Config file: '+xmlConfigFile)
        
        source = open(xmlConfigFile,'rb')
        tree = ET.parse(source)
        root = tree.getroot() 
        root_tag = root.tag
        #print(root_tag)
        for cfg in root.findall('config'):
            pcpValue = cfg.find('processing_core_path').text
            opValue = cfg.find('osgeo_path').text
            tpValue = cfg.find('temporal_path').text
            clValue = cfg.find('clip_load').text
            lrValue = cfg.find('load_results').text
            crofValue = cfg.find('output_file').text
            aclipValue = cfg.find('alwaysclip').text
            self.dlg.inputProcessingApiURL.setText(str(pcpValue))
            QgsMessageLog.logMessage('Setting Processing Core Path: '+str(pcpValue))
            self.dlg.webViewApiStatus.load(QUrl(pcpValue))
            self.dlg.inputGdalOsgeoPath.setText(str(opValue))
            QgsMessageLog.logMessage('Setting OSGEO Path: '+str(opValue))
            self.dlg.inputSharedFolderPath.setText(str(tpValue))
            QgsMessageLog.logMessage('Setting Temporal Path: '+str(tpValue))
            QgsMessageLog.logMessage('Setting output file: '+str(crofValue))
            QgsMessageLog.logMessage('Option Load clipped: '+str(clValue))
            QgsMessageLog.logMessage('Option Load results: '+str(lrValue))
            QgsMessageLog.logMessage('Option Load alwaysclip: '+str(aclipValue))
            QgsMessageLog.logMessage('===========================================')
            #Checkboxes
            if str(clValue).lower()=='true':
                self.dlg.checkLoadClipped.setCheckState(True)
            if str(lrValue).lower()=='true':
                self.dlg.checkLoadCropRows.setCheckState(True)
            
            if str(aclipValue).lower()=='true':
                self.flagNoCropRaster = False
            else:
                self.flagNoCropRaster = True
        
        self.dlg.radioButtonSeed1.setAutoExclusive(False)
        self.dlg.radioButtonSeed2.setAutoExclusive(False)
        self.dlg.radioButtonSeed3.setAutoExclusive(False)
        self.dlg.radioButtonSeed4.setAutoExclusive(False)
        self.dlg.radioButtonSeed1.setChecked(False)
        self.dlg.radioButtonSeed2.setChecked(False)
        self.dlg.radioButtonSeed3.setChecked(False)
        self.dlg.radioButtonSeed4.setChecked(False)
        self.dlg.radioButtonSeed1.setAutoExclusive(True)
        self.dlg.radioButtonSeed2.setAutoExclusive(True)
        self.dlg.radioButtonSeed3.setAutoExclusive(True)
        self.dlg.radioButtonSeed4.setAutoExclusive(True)
        self.dlg.labelOutputSeed.setText('')
        QgsMessageLog.logMessage('Seed status reloaded')
        
        source.close()
        del source
        flagApiServerIsRunning = self.url_ok(pcpValue+"/imlive")
        #check is api server is running
        QgsMessageLog.logMessage('API Server running: '+str(flagApiServerIsRunning))

        if flagApiServerIsRunning==False:
            #hide api tab
            self.dlg.mainTabs.setTabEnabled(3,False)
        else:
            #show api tab
            self.dlg.mainTabs.setTabEnabled(3,True)
        

    def writeXMLFile(self,filenameXML,arrayXMLData):
        """Write XML File."""
        QgsMessageLog.logMessage('writing xml file: '+ filenameXML)
        root = cET.Element('croprows')
        filenameSubElement = cET.SubElement(root,'filename')
        filenameSubElement.set('name',arrayXMLData[1])
        filenameSubElement.set('mask',arrayXMLData[2])
        idValue = cET.SubElement(filenameSubElement, 'image_dimensions')
        idValue.text = arrayXMLData[4]
        ioValue = cET.SubElement(filenameSubElement, 'image_origin')
        ioValue.text = arrayXMLData[6]
        psValue = cET.SubElement(filenameSubElement, 'pixel_size')
        psValue.text = arrayXMLData[3]
        ieValue = cET.SubElement(filenameSubElement, 'image_extents')
        ieValue.text = arrayXMLData[5]
        epsgValue = cET.SubElement(filenameSubElement, 'epsg')
        epsgValue.text = arrayXMLData[7]
        wtkValue = cET.SubElement(filenameSubElement, 'projwtk')
        wtkValue.text = arrayXMLData[8]
        seedValue = cET.SubElement(filenameSubElement, 'seed')
        seedValue.text = arrayXMLData[0]
        prjValue = cET.SubElement(filenameSubElement, 'prj')
        prjValue.text = arrayXMLData[9]
        rootStringData = cET.tostring(root)
        tree = ET.ElementTree(ET.fromstring(rootStringData))
        xmlCropRowsProjectFile = self.dlg.inputSharedFolderPath.text().replace("/", "\\")+filenameXML
        tree.write(xmlCropRowsProjectFile, encoding="utf-8", xml_declaration=True)
        #myfile = open(xmlCropRowsProjectFile, "w")
        #myfile.write(rootStringData)
        #tree.write(open(temporalPath+'croprows_shared.xml', 'w'), encoding='utf-8')
        pass
        return 1
    
    def fileNameDialog_Clicked(self,b):
        """File name dialog is clicked"""
        self.openFileNameDialog()

    def openFileNameDialog(self):
        """Open filename dialog.""" 
        #fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        #if fileName:
        #    print(fileName)
        w = QWidget()
        fileNameResponse = QFileDialog.getSaveFileName(w, 'Save Crop Rows Result File', '/temporal/croprows_output_file.shp',"ESRI Shapefile (*.shp)")
        if fileNameResponse != '':
            #self.dlg.outputfilename.setText(str(filename))
            QgsMessageLog.logMessage('Set output crop rows filename: '+ str(fileNameResponse))
        else:
            QgsMessageLog.logMessage('You must be set a croprows filename')
            QMessageBox.critical(None,'Error!',"You must be set a croprows filename!", QMessageBox.Ok)

    def executeCropRowsClipProcessing(self):
        """Execute Crop Rows STEP 1"""
        QgsMessageLog.logMessage('Excecute Task1: Clip Raster Mosaic by Vector Mask')
        strMosaicRasterFileSelected = self.dlg.comboBoxInputRaster.currentText()
        strMaskVectorFileSelected = self.dlg.comboBoxInputVector.currentText()
        
        seedValue=0
        QgsMessageLog.logMessage('Get Seed from user selection')
        if self.dlg.radioButtonSeed1.isChecked() == True:
            seedValue=1
        elif self.dlg.radioButtonSeed2.isChecked() == True:
            seedValue=2
        elif self.dlg.radioButtonSeed3.isChecked() == True:
            seedValue=3
        elif self.dlg.radioButtonSeed4.isChecked() == True:
            seedValue=4
        
        if(seedValue==0):
            QgsMessageLog.logMessage('You must be set a seed value !')
            QMessageBox.critical(None,'Error!',"You must be set a <b>seed</b> value !", QMessageBox.Ok)
            pass
        else:
            QgsMessageLog.logMessage('Seed value: '+str(seedValue))

        #Start Crop Rows processing
        if strMosaicRasterFileSelected != '' and strMaskVectorFileSelected != '' and seedValue > 0 and self.flagClipTaskDone==0:
            if self.flagNoCropRaster == False:
                msgboxCrop = "Are you sure that you want to start a <b>Mosaic Clip by Mask</b> process?<br>Keep in mind this task can take a few minutes, even several hours."
            else:
                msgboxCrop = "Are you sure that you want to copy a raster <b>Mosaic</b> into a selected shared folder?<br>Keep in mind this process can take a few minutes, even several hours."
            ret = QMessageBox.question(None, "Mosaic Data Preprocessing", (msgboxCrop),QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ret == QMessageBox.Yes:
                #hide step1 button
                self.dlg.btnExecuteClippingTask.setVisible(False)
                QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                
                self.dlg.statusBarProcessing.setGeometry(10, 281, 631, 31)

                self.dlg.statusBarProcessing.setValue(1)
                QgsMessageLog.logMessage('Processing Raster ')
                #urlSourceRasterMosaic = QgsMapLayerRegistry.instance().mapLayersByName(strMosaicRasterFileSelected)[0].dataProvider().dataSourceUri()
                urlSourceRasterMosaic = QgsProject.instance().mapLayersByName(strMosaicRasterFileSelected)[0].dataProvider().dataSourceUri()
                self.dlg.statusBarProcessing.setValue(5)
                #urlSourceVectorMask = QgsMapLayerRegistry.instance().mapLayersByName(strMaskVectorFileSelected)[0].dataProvider().dataSourceUri()
                urlSourceVectorMask = QgsProject.instance().mapLayersByName(strMaskVectorFileSelected)[0].dataProvider().dataSourceUri()
                self.dlg.statusBarProcessing.setValue(10)
                urlSourceVectorMaskSplit = urlSourceVectorMask.split("|")[0]
                self.dlg.statusBarProcessing.setValue(20)
                temporalPath = self.dlg.inputSharedFolderPath.text().replace("/", "\\")
                rasterLyr = QgsRasterLayer(urlSourceRasterMosaic, "masklayer")
                pixelSizeX = rasterLyr.rasterUnitsPerPixelX()
                pixelSizeY = rasterLyr.rasterUnitsPerPixelY()
                self.dlg.statusBarProcessing.setValue(25)
     
                QgsMessageLog.logMessage(str(urlSourceRasterMosaic))
                QgsMessageLog.logMessage(str(urlSourceVectorMaskSplit))
                QgsMessageLog.logMessage('GDAL Clipper')
                QgsMessageLog.logMessage(str(pixelSizeX))
                QgsMessageLog.logMessage(str(pixelSizeY))

                gdalOSGeoPath = self.dlg.inputGdalOsgeoPath.text().replace("/", "\\")
                #temporalPath = self.dlg.inputSharedFolderPath.text().replace("/", "\\")
                self.dlg.statusBarProcessing.setValue(30)
                timestr = time.strftime("%Y%m%d-%H%M%S")
                ouputFilenameRasterClip = 'clipfile_'+timestr+'.tif'
                ouputFilenameVectorMask = 'maskfile_'+timestr+'.shp'
                ouputFilenamePrj = 'croprows_'+timestr
                ouputFilenameCropRowsProjectXML = 'croprows_'+timestr+'.xml'
                ouputclipfile_path=os.path.join(temporalPath,ouputFilenameRasterClip)
                #temporalPath.replace("/", "\\") + ouputFilenameRasterClip
                self.dlg.statusBarProcessing.setValue(35)

                if self.flagNoCropRaster == True:
                    QgsMessageLog.logMessage('No Crop option selected - Copy file directly')
                    shutil.copyfile(urlSourceRasterMosaic, os.path.join(ouputclipfile_path[:-4]+'.tif' ) )
                    self.dlg.statusBarProcessing.setValue(40)
                else:
                    QgsMessageLog.logMessage('Crop raster by mask option selected - Cliping using GDAL')
                    #print('C:/Program Files/QGIS 2.14/bin/gdalwarp')
                    gdalWarpSubProcessCommand = '"'+gdalOSGeoPath+"\\"+'gdalwarp.exe" -dstnodata -9999 -q -cutline '+urlSourceVectorMaskSplit.replace("/", "\\")+' -crop_to_cutline -tr '+str(pixelSizeX)+' '+str(pixelSizeX)+' -of GTiff '+urlSourceRasterMosaic.replace("/", "\\")+' ' + ouputclipfile_path
                    QgsMessageLog.logMessage(str(gdalWarpSubProcessCommand))
                    self.dlg.statusBarProcessing.setValue(40)
                    p = subprocess.Popen(gdalWarpSubProcessCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    for line in p.stdout.readlines():
                        print (line),
                        retval = p.wait()
                
                self.dlg.statusBarProcessing.setValue(50)
                QgsMessageLog.logMessage('Clipper process done check result file ' + ouputclipfile_path)
                #Load result file into map environment
                rasterLayerClipped = QgsRasterLayer(ouputclipfile_path, ouputFilenameRasterClip[:-4])

                pixelSizeXClip = rasterLayerClipped.rasterUnitsPerPixelX()
                pixelSizeYClip = rasterLayerClipped.rasterUnitsPerPixelY()

                imageWClip = rasterLayerClipped.width()
                imageHClip = rasterLayerClipped.height()

                providerRasterLayerClipped = rasterLayerClipped.dataProvider()
                extentRasterLayerClipped = rasterLayerClipped.extent()

                #print(providerRasterLayerClipped)
                #xmin,ymax,xmax,ymin
                imageXminClip=(extentRasterLayerClipped.xMinimum())
                imageYminClip=(extentRasterLayerClipped.yMinimum())
                imageXmaxClip=(extentRasterLayerClipped.xMaximum())
                imageYmaxClip=(extentRasterLayerClipped.yMaximum())
                #origin
                imageXOriginClip=int(round(extentRasterLayerClipped.xMinimum()))
                imageYOriginClip=int(round(extentRasterLayerClipped.yMinimum()))
                #epsg 

                proj4crs=rasterLayerClipped.crs()

                QgsMessageLog.logMessage(str(proj4crs.srsid()))
                QgsMessageLog.logMessage(str(proj4crs.toProj4()))
                QgsMessageLog.logMessage(str(proj4crs.authid()))
                QgsMessageLog.logMessage(str(proj4crs.description()))
                QgsMessageLog.logMessage(str(proj4crs.ellipsoidAcronym()))
                QgsMessageLog.logMessage(str(proj4crs.findMatchingProj()))
                QgsMessageLog.logMessage(str(proj4crs.postgisSrid()))
                QgsMessageLog.logMessage(str(proj4crs.toWkt()))

                epsgClip = proj4crs.postgisSrid()
                epsgWKTClip = proj4crs.toWkt()

                #QgsMapLayerRegistry.instance().addMapLayer(rasterLayerClipped)
                QgsProject.instance().addMapLayer(rasterLayerClipped)
                #pass

                self.dlg.statusBarProcessing.setValue(75)
                #copy vector mask
                outputFileMaskPath=os.path.join(temporalPath,ouputFilenameVectorMask)
                #temporalPath.replace("/", "\\") + ouputFilenameVectorMask
                temporalVectorLayer = QgsVectorLayer(urlSourceVectorMaskSplit, "tmp_polygon", "ogr")
                shutil.copyfile(urlSourceVectorMaskSplit[:-4]+'.shp', os.path.join(outputFileMaskPath[:-4]+'.shp' ) )
                shutil.copyfile(urlSourceVectorMaskSplit[:-4]+'.dbf', os.path.join(outputFileMaskPath[:-4]+'.dbf' ) )
                shutil.copyfile(urlSourceVectorMaskSplit[:-4]+'.shx', os.path.join(outputFileMaskPath[:-4]+'.shx' ) )
                temporalVectorLayerDataProvider=temporalVectorLayer.dataProvider()
                temporalVectorLayerCrs=temporalVectorLayerDataProvider.crs()
                temporalVectorLayerCrsString=temporalVectorLayerCrs.authid()
                temporalVectorLayerEPSGInt=int(temporalVectorLayerCrsString[5:])

                QgsMessageLog.logMessage(str(temporalVectorLayerEPSGInt))
                maskVectorLayerExported = QgsVectorLayer(outputFileMaskPath,ouputFilenameVectorMask[:-4],"ogr")
                crs = maskVectorLayerExported.crs()
                crs.createFromId(temporalVectorLayerEPSGInt)
                maskVectorLayerExported.setCrs(crs)
                maskVectorLayerExported.setCrs(QgsCoordinateReferenceSystem(temporalVectorLayerEPSGInt, QgsCoordinateReferenceSystem.EpsgCrsId))

                styleBoundary = os.path.join((os.path.dirname(os.path.abspath(__file__))),'styles', 'croprows_style_boundary.qml' )
                maskVectorLayerExported.loadNamedStyle(styleBoundary)
                #QgsMapLayerRegistry.instance().addMapLayer(maskVectorLayerExported)
                QgsProject.instance().addMapLayer(maskVectorLayerExported)
                
                #end copy vector mask

                #TODO: try not to simulate process status, make it real
                for i in range(76, 90):
                    self.dlg.statusBarProcessing.setValue(i)

                #show step2 button 
                self.dlg.btnExecuteProcessingFromApi.setVisible(True)

                self.dlg.statusBarProcessing.setValue(95)
                
                arrXMLOptions = [
                    str(seedValue), 
                    str(ouputFilenameRasterClip), 
                    str(ouputFilenameVectorMask), 
                    str(pixelSizeXClip)+',-'+str(pixelSizeYClip),
                    str(imageWClip)+','+str(imageHClip),
                    str(imageXminClip)+','+str(imageYminClip)+','+str(imageXmaxClip)+','+str(imageYmaxClip),
                    str(imageXOriginClip)+','+str(imageYOriginClip),
                    str(epsgClip),
                    str(epsgWKTClip),
                    str(ouputFilenamePrj)
                    ]

                #Write XML file
                self.writeXMLFile(ouputFilenameCropRowsProjectXML,arrXMLOptions)

                self.dlg.xmlCoreFile.setText(str(ouputFilenameCropRowsProjectXML))

                self.dlg.statusBarProcessing.setValue(100)

                QApplication.setOverrideCursor(QtCore.Qt.ArrowCursor)

                self.flagClipTaskDone = 1
                
                toStep2Msg = QMessageBox.question(None, "Crop Rows processing task start", ("Are you sure that you want to start a <b>Crop Rows</b> processing task ?<br>Keep in mind this process can take a few minutes, even several hours.<br><br>Make sure that <b>Crop Rows - API Server is Running before continue.</b>"),QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if toStep2Msg == QMessageBox.Yes:
                    QgsMessageLog.logMessage('Run Step 2')
                    self.executeCropRowsProcessingFromAPI()
                    pass
                else:
                    QMessageBox.information(None,'Message !',"You must be run the processing task by manually way !<br>Just click on the button <b>Processing Task (manual)</b>", QMessageBox.Ok)
                    pass
            else:
                QgsMessageLog.logMessage('No Mosaic Clip Process Selected')
                pass
        else:
            QgsMessageLog.logMessage('Missing Required Parameters')
            QgsMessageLog.logMessage('strMosaicRasterFileSelected: '+strMosaicRasterFileSelected)
            QgsMessageLog.logMessage('strMaskVectorFileSelected: '+strMaskVectorFileSelected)
            QgsMessageLog.logMessage('seedValue: '+str(seedValue))
            QgsMessageLog.logMessage('flagClipTaskDone: '+str(self.flagClipTaskDone))
            QMessageBox.critical(None,'Error!',"Missing Required Parameter !", QMessageBox.Ok)
    pass


    """
    STEP 2
    """
    def executeCropRowsProcessingFromAPI(self):
        """Execute Crop Rows STEP 2"""
        flagApiServerIsRunning = self.url_ok(self.dlg.inputProcessingApiURL.text()+'/imlive')
        #check is api server is running
        QgsMessageLog.logMessage('API Server running: '+str(flagApiServerIsRunning))
        if flagApiServerIsRunning==False:
            QMessageBox.critical(None,'Message !',"<b>Crop Rows API Server is NOT running !</b><br>Check Configuration TAB", QMessageBox.Ok)
            pass
        else:
            
            #show processing tab
            self.dlg.mainTabs.setTabEnabled(1,True)
            #move to processing tab
            self.dlg.mainTabs.setCurrentIndex(1)
            #hide step2 button if the processing task is running
            self.dlg.btnExecuteProcessingFromApi.setVisible(False)
            #adjust status bar
            self.dlg.statusBarProcessing2.setGeometry(10, 270, 611, 31) #23)

            #excecute task
            QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.dlg.statusBarProcessing2.setValue(10)
            strNewFile='croprows/'+str(self.dlg.xmlCoreFile.text())
            self.dlg.statusBarProcessing2.setValue(50)
            urlp = urlparse.urljoin(self.dlg.inputProcessingApiURL.text(),strNewFile)
            self.dlg.webViewProcessingStatus.load( QUrl(urlp))
            self.dlg.statusBarProcessing2.setValue(55)
            QgsMessageLog.logMessage('Crop Rows Generation processing from API Running')

    
    #def load_progress(self, load):
    #   QgsMessageLog.logMessage('Load progress: ' + str(load) , tag="CropRows Generator", level=QgsMessageLog.INFO)
        # if load == 100:
            #print('Fasle')
        #else:
            #print('True')

    def on_webViewProcessingStatus_loadFinished(self):
        """Task done"""
        QgsMessageLog.logMessage('Load results')
        self.dlg.statusBarProcessing2.setValue(60)
        xmlCropRowsResultsProcessing=(os.path.join(self.dlg.inputSharedFolderPath.text(),'results',('results_'+self.dlg.xmlCoreFile.text())))
        #check if result file exists
        QgsMessageLog.logMessage('XML Result File: '+str(xmlCropRowsResultsProcessing))
        QgsMessageLog.logMessage('results_'+self.dlg.xmlCoreFile.text())
        self.dlg.statusBarProcessing2.setValue(65)
        
        if(os.path.exists(xmlCropRowsResultsProcessing)==False):
            #print("No croprows result file found !")
            QgsMessageLog.logMessage('No croprows result file found !')
        else:
            source = open(xmlCropRowsResultsProcessing,'rb')
            tree = ET.parse(source)
            root = tree.getroot()
            for filexml in root.findall('filename'):
                resultVectorialFile = filexml.find('result').text
                resultVectorialBufferFile = filexml.find('buffer').text
                #print(resultVectorialFile)
                QgsMessageLog.logMessage(str(resultVectorialFile))
                QgsMessageLog.logMessage(str(resultVectorialBufferFile))
                resultTileFile = filexml.find('tile').text
                #print(resultTileFile)
                QgsMessageLog.logMessage(str(resultTileFile))
                self.dlg.statusBarProcessing2.setValue(60)
                #load result into qgis
                temporalPath = self.dlg.inputSharedFolderPath.text().replace("/", "\\")
                outputFileMaskPath=os.path.join(temporalPath,"results",resultVectorialFile)
                outputFileMaskBufferPath=os.path.join(temporalPath,"results",resultVectorialBufferFile)
                
                maskVectorLayerExported = QgsVectorLayer(outputFileMaskPath,"croprows_lines","ogr")
                maskVectorLayerBufferExported = QgsVectorLayer(outputFileMaskBufferPath,"croprows_lines_buffer","ogr")
                self.dlg.statusBarProcessing2.setValue(70)
                #style for croprows lines result shapefile
                styleCropRows = os.path.join((os.path.dirname(os.path.abspath(__file__))),'styles', 'croprows_style_croplines.qml' )
                maskVectorLayerExported.loadNamedStyle(styleCropRows)
                #QgsMapLayerRegistry.instance().addMapLayer(maskVectorLayerExported)
                QgsProject.instance().addMapLayer(maskVectorLayerExported)
                self.dlg.statusBarProcessing2.setValue(80)

                #style for buffer croprows lines result shapefile
                styleCropRowsBuf = os.path.join((os.path.dirname(os.path.abspath(__file__))),'styles', 'croprows_style_buffer.qml' )
                maskVectorLayerBufferExported.loadNamedStyle(styleCropRowsBuf)
                #QgsMapLayerRegistry.instance().addMapLayer(maskVectorLayerBufferExported)
                QgsProject.instance().addMapLayer(maskVectorLayerBufferExported)
                self.dlg.statusBarProcessing2.setValue(85)

                outputFileTilePath=os.path.join(temporalPath,"results",resultTileFile)
                maskVectorLayerTileExported = QgsVectorLayer(outputFileTilePath,"croprows_tiles","ogr")
                self.dlg.statusBarProcessing2.setValue(90)
                #style for croprows tiles geojson
                styleTiles = os.path.join((os.path.dirname(os.path.abspath(__file__))),'styles', 'croprows_style_tileindex.qml' )
                maskVectorLayerTileExported.loadNamedStyle(styleTiles)
                #QgsMapLayerRegistry.instance().addMapLayer(maskVectorLayerTileExported)
                QgsProject.instance().addMapLayer(maskVectorLayerTileExported)

                self.dlg.outputfilename.setText(str(outputFileMaskPath))
            self.dlg.statusBarProcessing2.setValue(100)
            source.close()
            del source
        QApplication.setOverrideCursor(QtCore.Qt.ArrowCursor)
        QMessageBox.information(None,'Message !',"Crop Rows Generation Done !<br><b>Check Crop Rows Results ! <b/>", QMessageBox.Ok)
        self.dlg.close()
        reloadPlugin('PACropRows')
        #close all qgis application
        #QtCore.QCoreApplication.instance().quit()

    def displaySeedSelectedRadioOption(self,strName):
        """Seed Selected"""
        QgsMessageLog.logMessage('Seed Selected')
        QgsMessageLog.logMessage(str(strName))
        self.dlg.labelOutputSeed.setText('Seed Selected: <b>' + strName + '</b>' )
    
    def saveConfigXMLAndReloadPlugin(self):
        """Save config and reload"""
        QgsMessageLog.logMessage('Reading configuration file')
        
        xmlConfigFile = os.path.join((os.path.dirname(os.path.abspath(__file__))), 'config.xml' )
        QgsMessageLog.logMessage('Config file:'+xmlConfigFile)
        
        tree = ET.parse(xmlConfigFile)
        root = tree.getroot() 
        root_tag = root.tag

        for cfg in root.iter('config'):
            cfg.find('processing_core_path').text = self.dlg.inputProcessingApiURL.text()
            cfg.find('osgeo_path').text = self.dlg.inputGdalOsgeoPath.text()
            cfg.find('temporal_path').text =  self.dlg.inputSharedFolderPath.text()
        tree.write(xmlConfigFile)

        QgsMessageLog.logMessage('Current Configuration Saved')

        QMessageBox.information(None,'Configuration Message',"Current Configuration Saved !", QMessageBox.Ok)                  
        self.dlg.close()
        reloadPlugin('PACropRows')
        #self.readConfigFileFromXML()
    
    def cancelWizard(self):
        QgsMessageLog.logMessage('Cancel Wizard')
        self.dlg.close()
        reloadPlugin('PACropRows')

    def reload_plugin(self):
        """Reload Plugin"""
        reloadPlugin('PACropRows')
    
    #def run(self):
    #    self.dlg.show()
    #    result = self.dlg.exec_()
    #    if result:
    #        pass
        
    def run(self):
        """Run method that performs all the real work"""
        self.dlg.statusBarProcessing.setValue(0)
        #show step1 button
        self.dlg.btnExecuteClippingTask.setVisible(True)
        #self.dlg.textEdit.clear()
        ## Load layers and add to comboboxes
        #layers = self.iface.legendInterface().layers()
        #layers = QgsMapLayerRegistry.instance().mapLayers().values()
        layers = QgsProject.instance().mapLayers().values()
        #Clear combobox
        self.dlg.comboBoxInputVector.clear()
        self.dlg.comboBoxInputRaster.clear()
        #layer_list = []
        for layer in layers:
            #if layer.type() == QgsMapLayer.VectorLayer and (layer.wkbType()==QGis.WKBPolygon or layer.wkbType() == QGis.WKBMultiPolygon):
            if layer.type() == QgsMapLayer.VectorLayer and (layer.wkbType()==QgsWkbTypes.Polygon or layer.wkbType() == QgsWkbTypes.MultiPolygon):
                self.dlg.comboBoxInputVector.addItem(layer.name(), layer)
            if layer.type() == QgsMapLayer.RasterLayer:
                self.dlg.comboBoxInputRaster.addItem(layer.name(), layer)
            #layer_list.append(layer.name())
        #self.dlg.comboBoxInputVector.addItems(layer_list)

        self.dlg.textAboutThesis.clear()
        self.dlg.textAboutThesis.append("<span><b>Crop Rows Generator (CRG) QGIS-PLUGIN</b> is part of: <br><b>AN AUTOMATIC CROP ROWS GENERATOR USING AERIAL HIGH-RESOLUTION IMAGES FOR PRECISION AGRICULTURE</b>,master research project.</span>")
        self.dlg.textAboutThesis.append("<span>Developed in partial fulfillment of the requirements for the degree of:</span>")
        self.dlg.textAboutThesis.append("<span><b>Magister en Ingenier&iacute;a con &Eacute;nfasis en Ingenier&iacute;a de Sistemas y Computaci&oacute;n</b></span>")
        strFromLocalFile = os.path.abspath(os.path.join(os.path.dirname(__file__), "help.html"))
        urlFromLocalFile = QUrl.fromLocalFile(strFromLocalFile)
        #self.dlg.webViewHelp.load(QUrl('http://www.google.com'))
        self.dlg.webViewHelp.load(urlFromLocalFile)
        str2FromLocalFile = os.path.abspath(os.path.join(os.path.dirname(__file__), "noprocessing.html"))
        url2FromLocalFile = QUrl.fromLocalFile(str2FromLocalFile)
        self.dlg.webViewApiStatus.load(url2FromLocalFile)
        #self.dlg.pushButtonOutputVectorFile.clicked.connect(self.fileNameDialog_Clicked)
        self.dlg.btnExecuteClippingTask.clicked.connect(self.executeCropRowsClipProcessing)
        self.dlg.btnExecuteProcessingFromApi.clicked.connect(self.executeCropRowsProcessingFromAPI)
        self.dlg.webViewProcessingStatus.loadFinished.connect(self.on_webViewProcessingStatus_loadFinished)
        self.dlg.radioButtonSeed1.clicked.connect(partial(self.displaySeedSelectedRadioOption,"Horizontal Pattern"))
        self.dlg.radioButtonSeed2.clicked.connect(partial(self.displaySeedSelectedRadioOption,"Vertical Pattern"))
        self.dlg.radioButtonSeed3.clicked.connect(partial(self.displaySeedSelectedRadioOption,"Counterclockwise Pattern"))
        self.dlg.radioButtonSeed4.clicked.connect(partial(self.displaySeedSelectedRadioOption,"Clockwise Pattern"))
        self.dlg.btnExecuteSaveConfig.clicked.connect(self.saveConfigXMLAndReloadPlugin)
        #wizard
        self.dlg.btnCancelWizard.clicked.connect(self.cancelWizard)
        #hide step2 button 
        self.dlg.btnExecuteProcessingFromApi.setVisible(False)
        #hide processing tab
        self.dlg.mainTabs.setTabEnabled(1,False)

        self.dlg.statusBarProcessing.setGeometry(10, 281, 511, 31)
        
        nowTime = time.strftime("%c")
        QgsMessageLog.logMessage('========================================================')
        QgsMessageLog.logMessage('Crop Rows GUI dialog starts:'+time.strftime('%c'))
        QgsMessageLog.logMessage('========================================================')
        self.readConfigFileFromXML()
        #self.dlg.webViewProcessingStatus.loadProgress.connect(self.load_progress)
        # show the dialog
        #self.dlg.show()
        self.dlg.exec_()