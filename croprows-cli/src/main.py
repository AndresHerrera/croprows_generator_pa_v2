# -*- coding: UTF-8 -*-
"""Crop Rows Main.
    
    :author: Andres Herrera
    :begin: 2018-02-22
    :copyright: 2018 by Andres Herrera - Universidad del Valle
    :email: fabio.herrera@correounivalle.edu.co

    This program is free software; you can redistribute it and/or modify   it under the terms of the GNU General Public License as published by  the Free Software Foundation; either version 2 of the License, or 
    (at your option) any later version.  This script initializes the plugin, making it known to QGIS.

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>
"""

   

import sys
import os.path
import time
import croprows_globals as crglobals
from croprows_utils import printLogMsg
from croprows_fileutils import croprowsFileReader,CropRowsTilesGenerator,CropRowsAnglesGenerator,generateCropRowsLinesAll#as crfileutils
from croprows_geo import postProcessingLines

__package__ = 'croprows-cli'
__author__ = "Andres Herrera"
__copyright__ = "Copyright 2018, Crop Rows Generator CLI"
__credits__ = ["Andres Herrera", "Maria Patricia Uribe", "Ivan Mauricio Cabezas"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andres Herrera"
__email__ = "fabio.herrera@correounivalle.edu.co"
__status__ = "Development"

startTime = time.time()

##
##https://stackoverflow.com/questions/12689304/ctypes-error-libdc1394-error-failed-to-initialize-libdc1394
##sudo ln /dev/null /dev/raw1394
##

def cropRowsMain():
    
    """
    cropRowsMain.
    
    :param self: no input params
    :returns: None
    """

    if len(sys.argv)<2:
        printLogMsg(crglobals.SEPARATOR_MSG)
        print(crglobals.ERROR_MSG+"Fatal: You forgot to include the crop rows project file on the command line.")
        print("Usage: python %s <croprowsproject.xml>" % sys.argv[0])
        printLogMsg(crglobals.SEPARATOR_MSG)
        print(crglobals.HELP_MSG)
        sys.exit(1)
    
    if(sys.argv[1]=='-h'):
        print(crglobals.HELP_MSG)
        sys.exit(1)
    ######################################################
    ##Define processing vars
    ######################################################

    if len(sys.argv)>2:
        if(sys.argv[2]=='-p'):
            crglobals.PROCESSING_MODE = 'parallel'
        if(sys.argv[2]=='-s'):
            crglobals.PROCESSING_MODE = 'serial'
        if(sys.argv[2]=='-debug'):
            crglobals.DEBUGMODE = False
        if(sys.argv[2]=='-t'):
            crglobals.DEF_TILESIZE_M = int(sys.argv[3])
        if(sys.argv[2]=='-h'):
            print(crglobals.HELP_MSG)
               
    printLogMsg(crglobals.SEPARATOR_MSG)
    printLogMsg('Number of arguments: %s arguments.' % (len(sys.argv)) )
    printLogMsg('Argument List: %s arguments.' % str(sys.argv) )
    printLogMsg('Processing Mode : %s ' % str(crglobals.PROCESSING_MODE) )
    

    #imagePathResults = "../orthomosaics/"
    #shared folder for croprows cli
    imagePathResults = "orthomosaics/"
    cropRowsProjectFile =  sys.argv[1]

    #Read Crop Rows Project Config File
    crFileObject = croprowsFileReader(os.path.join(imagePathResults,cropRowsProjectFile)) 
    fileNameValue=crFileObject['filename']
    imageDimensionsValue=crFileObject['image_dimensions']
    imageOriginValue=crFileObject['image_origin']
    pixelSizeValue=crFileObject['pixel_size']
    imageExtentsValue=crFileObject['image_extents']
    epsgValue=crFileObject['epsg']
    projWKTValue=crFileObject['projwtk']
    seedValue=crFileObject['seed']
    maskValue=crFileObject['mask']
    prjValue=crFileObject['prj']

    ####################################################
    ## Crop Rows Tiles Generation
    ####################################################
    
    ## TODO: Perform a Parallel task 

    #Config tiles generation
    cfgTilesGenerator = [
        imagePathResults, 
        fileNameValue, 
        imageDimensionsValue,
        imageOriginValue,
        pixelSizeValue,
        imageExtentsValue,
        crglobals.DEF_TILESIZE_M,
        epsgValue,
        projWKTValue,
        prjValue]
    #Exec tilesGeneration task 

    #Create a new tilesGenerator Instance
    tilesGenerator = CropRowsTilesGenerator()
    tilesGenerator.tilesGeneration(cfgTilesGenerator)
    tilesDirName, nCols , nRows = tilesGenerator.getTilesGenerationGlobals()
    printLogMsg('->tilesDirName: %s \n->nRows: %s \n->nCols: %s ' % (tilesDirName,nRows,nCols))

    #Config angles generator
    cfgAnglesGenerator = [
        tilesDirName,
        nCols,
        nRows,
        seedValue,
        crglobals.SEED_SPAN
    ]
    #Exec anglesGeneration task
    anglesGenerator = CropRowsAnglesGenerator()
    anglesGenerator.anglesGeneration(cfgAnglesGenerator)
    anglesFoundArray, angleMean, angleSd = anglesGenerator.getAnglesGeneratorGlobals()  
    #Angles found 
    printLogMsg(crglobals.SEPARATOR_MSG)
    printLogMsg(anglesFoundArray)
    printLogMsg(crglobals.OK_MSG+'Mean Angle: %s' % (angleMean))
    printLogMsg(crglobals.OK_MSG+'Std Angle: %s' % (angleSd))
    printLogMsg(crglobals.SEPARATOR_MSG)

    #Generate Lines Config
    cfgLinesGenerator =[
        tilesDirName,
        angleMean,
        pixelSizeValue,
        imageExtentsValue,
        epsgValue,
        crglobals.DEF_TILESIZE_M,
        nCols,
        nRows
    ]
    #Exec generateLinesAll task
    generateCropRowsLinesAll(cfgLinesGenerator)

    cfgPostProcessingLines =[
        tilesDirName,
        epsgValue,
        nCols,
        nRows,
        imagePathResults+maskValue,
        seedValue
    ]
    
    #exec Post processing Lines task
    postProcessingLines(cfgPostProcessingLines)

    endTime = time.time()
    elapsedTime = endTime - startTime

    printLogMsg(crglobals.SEPARATOR_MSG)
    printLogMsg(crglobals.DONEEND_MSG+"Total Processing Time: "+str(round(elapsedTime,2)) + " seconds")
    printLogMsg(crglobals.DONEEND_MSG+'Data processed in %s mode ' % str(crglobals.PROCESSING_MODE) )
    printLogMsg(crglobals.SEPARATOR_MSG)
    printLogMsg(crglobals.BANNER_DONE)
    if(crglobals.DEBUGMODE==False):
        print(crglobals.DONE_MSG+'CROP ROWS GENERATION')
        print(crglobals.DONEEND_MSG+"Total Processing Time: "+str(round(elapsedTime,2)) + " seconds")

    
if __name__ == "__main__":
    cropRowsMain()
