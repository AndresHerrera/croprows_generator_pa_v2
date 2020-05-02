# -*- coding: UTF-8 -*-
"""Crop Rows Fileutils

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""
import croprows_globals as crglobals
import croprows_utils as crutils
import croprows_image_preprocessing as crimgprep
import imutils_perspective as imutils

import os
import time
import sys
import cv2
import math
import re
import shutil
import time
import json

import numpy as np
from PIL import Image

import xml.etree.ElementTree as ET
import xml.etree.cElementTree as cET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from joblib import Parallel, delayed
import multiprocessing
from multiprocessing import active_children

#https://github.com/zimeon/iiif/issues/11
#Confirm that warning can be silenced we adjusting the Image.MAX_IMAGE_PIXELS setting:
Image.MAX_IMAGE_PIXELS = crglobals.MAX_IMAGE_PIXELS_CFG

np.seterr(divide='ignore', invalid='ignore')



def croprowsFileReader(xmlProjectFile):

	"""
		croprowsFileReader.
		
		:param xmlProjectFile: (String) xmlProjectFile.
		:returns None: none.
	"""

	if(os.path.exists(xmlProjectFile)==False):
		sys.exit(crglobals.ERROR_MSG+"Fatal error crash in runnable thread file not found\nDescription: Check Crop Rows XML project file")
	
	tree = ET.parse(xmlProjectFile)
	root = tree.getroot()

	for fileXML in root.findall('filename'):
		fileNameValue = fileXML.get('name')
		maskValue = fileXML.get('mask')
		imageDimensionsValue = fileXML.find('image_dimensions').text
		imageOriginValue = fileXML.find('image_origin').text
		pixelSizeValue = fileXML.find('pixel_size').text
		imageExtentsValue = fileXML.find('image_extents').text
		epsgValue = fileXML.find('epsg').text
		projWKTValue = fileXML.find('projwtk').text
		seedValue = fileXML.find('seed').text
		prjValue = fileXML.find('prj').text

	#fileNameValue = "clip_orthomosaic.tif"
	#X,Y
	#imageDimensionsValue =[17992,23231]
	#X,Y
	#imageOriginValue = [358624,376856]
	#X,Y
	#pixelSizeValue = [0.0184399,-0.0184401]
	#xmin,ymax,xmax,ymin
	#imageExtentsValue = [358624.4387608282850124,376427.6166225711349398,358956.2094862160738558,376855.9995228421757929]
	#epsgValue=32618
	#projWKTValue='PROJCS["WGS 84 / UTM zone 18N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-75],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],AUTHORITY["EPSG","32618"],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
	#seed = 4
	#prj=prjname


	crutils.printLogMsg(crglobals.DONE_MSG+'Reading from CropRows project file: %s ' % (xmlProjectFile) )
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	crutils.printLogMsg('cfg -> filename: %s'%(str(fileNameValue)))
	crutils.printLogMsg('cfg -> mask: %s'%(str(maskValue)))
	crutils.printLogMsg('cfg -> image_dimensions: %s'%(str(imageDimensionsValue)))
	crutils.printLogMsg('cfg -> image_origin: %s'%(str(imageOriginValue)))
	crutils.printLogMsg('cfg -> pixel_size: %s'%(str(pixelSizeValue)))
	crutils.printLogMsg('cfg -> image_extents: %s'%(str(imageExtentsValue)))
	crutils.printLogMsg('cfg -> epsg: %s'%(str(epsgValue)))
	crutils.printLogMsg('cfg -> projwtk: %s'%(projWKTValue))
	crutils.printLogMsg("cfg -> seed: %s" % (seedValue))
	crutils.printLogMsg("cfg -> prj: %s" % (prjValue))
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)

	return {"filename":fileNameValue, 
	"image_dimensions":[int(imageDimensionsValue.split(',')[0]),int(imageDimensionsValue.split(',')[1])], 
	"image_origin": [int(imageOriginValue.split(',')[0]),int(imageOriginValue.split(',')[1])] , 
	"pixel_size": [float(pixelSizeValue.split(',')[0]),float(pixelSizeValue.split(',')[1])], 
	"image_extents": [float(imageExtentsValue.split(',')[0]),float(imageExtentsValue.split(',')[1]),float(imageExtentsValue.split(',')[2]),float(imageExtentsValue.split(',')[3])] , 
	"epsg": epsgValue , "projwtk": projWKTValue , "seed": int(seedValue) , "mask":maskValue , "prj":prjValue  }


class CropRowsTilesGenerator:
	
	dirName = ""
	nCols = 0
	nRows = 0


	def cropTileImageWorker(self,iCol,jRow,pixelTile,dirName,processingImageFile,optionForProcessing):
		"""Thread worker function for crop image into tiles"""
		
		"""
		cropTileImageWorker.
		
		:param iCol: (int) Columns.
		:param jRow: (int) Rows.
		:param pixelTile: (int) pixelTile.
		:param dirName: (String) dirName.
		:param processingImageFile: (Sting) processingImageFile.
		:param optionForProcessing: (String) optionForProcessing.
		:returns None: none.
		"""

		if(optionForProcessing=='parallel'):
			crutils.printLogMsg(crglobals.WORKER_MSG+"cropTileImageWorker -> Processing Tile %s , %s " % (str(iCol), str(jRow)  ) )
			name = multiprocessing.current_process().name
			crutils.printLogMsg(crglobals.START_MSG+'Process name: %s ' % (name))
			crutils.printLogMsg(crglobals.START_MSG+"Parent processs: %s" % (str( os.getppid() )) )
			crutils.printLogMsg(crglobals.START_MSG+"Process id: %s" % (str( os.getpid() )) )

			x2 = 0 + (int(iCol) * pixelTile)
			y2 = 0 + (int(jRow) * pixelTile)
			x1 = x2 - pixelTile
			y1 = y2 - pixelTile
			# create a box to crop with
			boxToCrop = (x1,y1,x2,y2)
			
			try:
				# create crop region
				try:
					# save cropped region	
					croppedTileImageFileName = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str( int(iCol) )+"-"+crglobals.ROWPREFIX+str( int(jRow) )+crglobals.JPG_EXT
					croppedTileImageFileObject = os.path.join(dirName,croppedTileImageFileName)
					if(os.path.exists(croppedTileImageFileObject)):
						crutils.printLogMsg(crglobals.CHECK_MSG+"Tile Image already exists ! - skip")
						pass
					else:
						rasterImage = Image.open(processingImageFile)
						rasterImage.load()
						crutils.printLogMsg("Raster Input -> Raster Format : %s \nRaster Size: %s \nRaster Mode: %s " % (rasterImage.format, rasterImage.size, rasterImage.mode)) 
						rasterCroppedRegion = rasterImage.crop(boxToCrop)
						crutils.printLogMsg("Crop Region -> Raster Format : %s \nRaster Size: %s \nRaster Mode: %s " % (rasterCroppedRegion.format, rasterCroppedRegion.size, rasterCroppedRegion.mode))
						rasterCroppedRegion.save(croppedTileImageFileObject)
						crutils.printLogMsg(crglobals.DONE_MSG+"Tile Image Generated: " + croppedTileImageFileName)
						rasterImage.close()
				except Exception  as e:
					print(e)
			except:
				crutils.printLogMsg(crglobals.ERROR_MSG+'Raster Crop process exception for tile: %s , %s' %  (str(iCol), str(jRow)  ) )
		elif(optionForProcessing=='serial'):
			print('serial')

			cols = range(0,iCol,1)
			rows = range(0,jRow,1)

			for i in cols:
				for j in rows:
					crutils.printLogMsg(crglobals.WORKER_MSG+"cropTileImageWorker -> Processing Tile %s , %s " % (str(i), str(j)  ) )
					name = multiprocessing.current_process().name
					crutils.printLogMsg(crglobals.START_MSG+'Process name: %s ' % (name))
					crutils.printLogMsg(crglobals.START_MSG+"Parent processs: %s" % (str( os.getppid() )) )
					crutils.printLogMsg(crglobals.START_MSG+"Process id: %s" % (str( os.getpid() )) )

					x2 = 0 + (int(i) * pixelTile)
					y2 = 0 + (int(j) * pixelTile)
					x1 = x2 - pixelTile
					y1 = y2 - pixelTile
					# create a box to crop with
					boxToCrop = (x1,y1,x2,y2)
					
					try:
						# create crop region
						try:
							# save cropped region	
							croppedTileImageFileName = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str( int(i) )+"-"+crglobals.ROWPREFIX+str( int(j) )+crglobals.JPG_EXT
							croppedTileImageFileObject = os.path.join(dirName,croppedTileImageFileName)
							if(os.path.exists(croppedTileImageFileObject)):
								crutils.printLogMsg(crglobals.CHECK_MSG+"Tile Image already exists ! - skip")
								pass
							else:
								rasterImage = Image.open(processingImageFile)
								rasterImage.load()
								crutils.printLogMsg("Raster Input -> Raster Format : %s \nRaster Size: %s \nRaster Mode: %s " % (rasterImage.format, rasterImage.size, rasterImage.mode)) 
								rasterCroppedRegion = rasterImage.crop(boxToCrop)
								crutils.printLogMsg("Crop Region -> Raster Format : %s \nRaster Size: %s \nRaster Mode: %s " % (rasterCroppedRegion.format, rasterCroppedRegion.size, rasterCroppedRegion.mode))
								rasterCroppedRegion.save(croppedTileImageFileObject)
								crutils.printLogMsg(crglobals.DONE_MSG+"Tile Image Generated: " + croppedTileImageFileName)
								rasterImage.close()
						except Exception  as e:
							print(e)
					except:
						crutils.printLogMsg(crglobals.ERROR_MSG+'Raster Crop process exception for tile: %s , %s' %  (str(i), str(j)  ) )
		return 1

	#def tilesGeneration(imagePath, fileNameValue, imageDimensionsValue,imageOriginValue,pixelSizeValue,imageExtentsValue,tileSizeValue,epsgValue,projWKTValue):

	def tilesGeneration(self,cfgTilesGenerator):
		imagePath=cfgTilesGenerator[0]
		fileNameValue=cfgTilesGenerator[1]
		imageDimensionsValue=cfgTilesGenerator[2]
		imageOriginValue=cfgTilesGenerator[3]
		pixelSizeValue=cfgTilesGenerator[4]
		imageExtentsValue=cfgTilesGenerator[5]
		tileSizeValue=cfgTilesGenerator[6]
		epsgValue=cfgTilesGenerator[7]
		projWKTValue=cfgTilesGenerator[8]
		prjValue=cfgTilesGenerator[9]

		"""
		tilesGeneration.
		
		:param cfgTilesGenerator: (Array) config file tiles generator.
		:returns None: none.
		"""

		#imagePath = "orthomosaics/"
		processingImageFile = imagePath+fileNameValue
		crutils.printLogMsg("Image File to process: %s" % (processingImageFile))

		#cropDir = imagePath+crglobals.CROPDIR
		cropDirParentFolder = "".join((imagePath,crglobals.CROPDIR))
		cropDir = "".join((imagePath,crglobals.CROPDIR,prjValue,os.sep))
		crutils.printLogMsg("Results Folder : %s" % (cropDir))

		#raster =Image.open(processingImageFile)
		#crutils.printLogMsg("Raster Format : %s \nRaster Size: %s \nRaster Mode: %s \nRaster Info: %s " % (raster.format, raster.size, raster.mode, raster.info))   

		## Read from metadata file 
		## TODO: From Crop rows plugin create a XML file with the following contents

		# Dimensions X Y
		# Coords origin X Y
		# Pixel size
		# Projection
		# Extents
		# Bands Number

		#imageDimensionsValue =[17992,23231]
		#imageOriginValue = [358624,376856]
		#pixelSizeValue = [0.0184399,-0.0184401]
		#xmin,ymax,xmax,ymin
		#imageExtentsValue = [358624.4387608282850124,376427.6166225711349398,358956.2094862160738558,376855.9995228421757929]

		#Tile size for croping (meters)
		#tileSizeValue = 20
		crutils.printLogMsg("Tile Size m: %s" % (tileSizeValue))

		## for generate 20 meters tiles
		cmPerPixel = (pixelSizeValue[0])*100
		crutils.printLogMsg("CM per Pixel: %s" % (cmPerPixel))

		imageWTerrain = imageDimensionsValue[0]*cmPerPixel
		imageHTerrain = imageDimensionsValue[1]*cmPerPixel
		crutils.printLogMsg("Image W Terrain: %s" % (imageWTerrain))
		crutils.printLogMsg("Image H Terrain: %s" % (imageHTerrain))

		imageAreaTerrain = imageWTerrain * imageHTerrain
		imageAreaTerrainSqm = (imageWTerrain/100) * (imageHTerrain/100)
		crutils.printLogMsg("Image Area Terrain cm2: %s" % (imageAreaTerrain))
		crutils.printLogMsg("Image Area Terrain m2: %s" % (imageAreaTerrainSqm))
		crutils.printLogMsg("Image Area Terrain ha: %s" % (imageAreaTerrainSqm/10000))

		pixelTile = (tileSizeValue*100)/cmPerPixel
		crutils.printLogMsg("Pixel Tile: %s - %s" % (pixelTile , int(pixelTile) ))

		nCols = int(imageDimensionsValue[0] / pixelTile)+2
		nRows = int(imageDimensionsValue[1] / pixelTile)+2

		nTiles = nCols * nRows

		crutils.printLogMsg("nCols : %s nRows:  %s" % (nCols , nRows ))
		crutils.printLogMsg("nTiles : %s " % (nTiles))

		cols = range(0,nCols,1)
		rows = range(0,nRows,1)

		dirNameCropResults = cropDir
		crutils.printLogMsg("Results Directory : %s " % (dirNameCropResults))
		dirName = cropDir+crglobals.PICNAME+"_"+str(nCols)+"_"+str(nRows)+"_"+str(int(pixelTile))+"px"+"_"+str(nTiles)+"_"+crglobals.TILESENDNAME
		crutils.printLogMsg("Directory Name : %s " % (dirName))
		dirNameVectorResults =os.path.join(dirName,crglobals.VECTORDIR)
		crutils.printLogMsg("Directory Name for Vectors : %s " % (dirNameVectorResults))
		dirNameVectorObjResults =os.path.join(dirNameVectorResults,crglobals.OBJDIR)
		crutils.printLogMsg("Directory Name for Vectors(Objects) : %s " % (dirNameVectorObjResults))
		dirNameRasterResults =os.path.join(dirName,crglobals.RASTERDIR)
		crutils.printLogMsg("Directory Name for Rasters : %s " % (dirNameRasterResults))
		dirNameObjResults = os.path.join(dirName,crglobals.OBJDIR)
		crutils.printLogMsg("Directory Name (Objects) : %s " % (dirNameObjResults))
		dirNameExportResults =os.path.join(dirName,crglobals.EXPORTDIR)
		crutils.printLogMsg("Directory Name for Export Results : %s " % (dirNameExportResults))

		#Make all requeried folders if are necessary
		crutils.makeDirectory(cropDirParentFolder)
		crutils.makeDirectory(dirNameCropResults)
		crutils.makeDirectory(dirName)
		crutils.makeDirectory(dirNameVectorResults)
		crutils.makeDirectory(dirNameRasterResults)
		crutils.makeDirectory(dirNameObjResults)
		crutils.makeDirectory(dirNameVectorObjResults)
		crutils.makeDirectory(dirNameExportResults)
			
		crutils.printLogMsg(crglobals.OK_MSG+"Generating " + str(nTiles) + " tiles, in directory " + imagePath)
		startTime = time.time()
		totaltiles = nCols * nRows
		flagCurrent = 0

		crutils.printLogMsg(crglobals.SEPARATOR_MSG)
		
		#TODO: Just for testing, parallel mode or serial mode which one is faster ?
		flagModeProcessing = crglobals.PROCESSING_MODE

		crutils.printLogMsg(crglobals.CHECK_MSG+"Mode Processing:  %s" % (flagModeProcessing))

		if(flagModeProcessing=='parallel'):
			############################################################################################
			#Multiprocessing Task
			processingCores = (multiprocessing.cpu_count())
			crutils.printLogMsg(crglobals.CHECK_MSG+"Number of CPU cores: %s" % (str(processingCores)) )
			crutils.printLogMsg(crglobals.SEPARATOR_MSG)
			processingPool = multiprocessing.Pool(processes=(processingCores+2))
			results = [processingPool.apply(self.cropTileImageWorker, args=(i,j,pixelTile,dirName,processingImageFile,'parallel')) for i in range(nCols) for j in range(nRows)]
			processingPool.close()
			processingPool.join()
			crutils.printLogMsg(crglobals.DONEEND_MSG+"All Crop Tile Image Jobs Finished " )
			############################################################################################
		elif(flagModeProcessing=='serial'):
			self.cropTileImageWorker(nCols,nRows,pixelTile,dirName,processingImageFile,'serial')

		geoJsonTileFileName = 'tilemaster_'+crglobals.PICNAME+"_"+str(nCols)+"_"+str(nRows)+"_"+str(int(pixelTile))+"px"+"_"+str(nTiles)+"_"+crglobals.TILESENDNAME+crglobals.GEOJSON_EXT
		geoJsonTileFileObject = open(os.path.join(dirName,crglobals.VECTORDIR,geoJsonTileFileName),'w')
		polygonObjGeoJson='{"type": "FeatureCollection","crs": { "type": "name", "properties": '
		polygonObjGeoJson+='{ "name": "urn:ogc:def:crs:EPSG::'+str(epsgValue)+'" } },"features":[ '
		tileCoords=""

		for i in cols:
			for j in rows:
				crutils.printLogMsg(crglobals.SEPARATOR_MSG)
				
				flagCurrent+=1
				flagStatus = int(((flagCurrent)/totaltiles)*100)
				crutils.printLogMsg(crglobals.START_MSG+"Processing Tile %s , %s - Status: %s %% " % (str(i), str(j) , str(flagStatus) ) )
				
				#crutils.printLogMsg('======  Generate World File  =======')
				worldJPGXImageFileName = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str(i)+"-"+crglobals.ROWPREFIX+str(j)+crglobals.JPGX_EXT
				worldJPGXImageFileObject = os.path.join(dirName,worldJPGXImageFileName)
				worldJPGXFile = open(worldJPGXImageFileObject,'w')
				worldJPGXFile.write(str(pixelSizeValue[0]))
				worldJPGXFile.write('\n')
				worldJPGXFile.write('0.0')
				worldJPGXFile.write('\n')
				worldJPGXFile.write('0.0')
				worldJPGXFile.write('\n')
				worldJPGXFile.write(str(pixelSizeValue[1]))
				worldJPGXFile.write('\n')
				C = (i-1)*tileSizeValue
				F = (j-1)*(tileSizeValue*-1)
				coordinateX=imageExtentsValue[0]+C
				coordinateY=imageExtentsValue[3]+F
				worldJPGXFile.write(str(coordinateX))
				worldJPGXFile.write('\n')
				worldJPGXFile.write(str(coordinateY))
				worldJPGXFile.close()
				crutils.printLogMsg(crglobals.DONE_MSG+"World file: " + worldJPGXImageFileName)
				#crutils.printLogMsg('======  World File Generated  =======')

				#crutils.printLogMsg('======  Generate GeoJSON File  =======')
				geoJSONVectorFileName = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str(i)+"-"+crglobals.ROWPREFIX+str(j)+crglobals.GEOJSON_EXT
				geoJSONVectorFileNameObj = os.path.join(dirNameVectorResults,geoJSONVectorFileName)
				geoJsonFile = open(geoJSONVectorFileNameObj,'w')
				geoJSONPolygonTile='{"type": "FeatureCollection","crs": { "type": "name", "properties": '
				geoJSONPolygonTile+='{ "name": "urn:ogc:def:crs:EPSG::'+str(epsgValue)+'" } },"features": '
				geoJSONPolygonTile+='[{ "type": "Feature", "properties": { "col": '+str(i)+' , "row": '+str(j)+' , "generator": "Crop Rows Generator CLI" }, '
				geoJSONPolygonTile+='"geometry": { "type": "Polygon", '
				geoJSONPolygonTile+='"coordinates": [ [ [ '+str(coordinateX)+', '+str(coordinateY)+' ],'
				geoJSONPolygonTile+='[ '+str(coordinateX+tileSizeValue)+', '+str(coordinateY)+' ], '
				geoJSONPolygonTile+='[ '+str(coordinateX+tileSizeValue)+', '+str(coordinateY+(tileSizeValue*-1))+' ], '
				geoJSONPolygonTile+='[ '+str(coordinateX)+', '+str(coordinateY+(tileSizeValue*-1))+' ], '
				geoJSONPolygonTile+='[ '+str(coordinateX)+', '+str(coordinateY)+'] ] ] } }]}'
				geoJsonFile.write(geoJSONPolygonTile)
				geoJsonFile.close()
				crutils.printLogMsg(crglobals.DONE_MSG+"GeoJSON file: " + geoJSONVectorFileName)
				#crutils.printLogMsg('======  GeoJSON File Generated  =======')
				tileCoords+='{ "type": "Feature", "properties": { "col": '+str(i)+' , "row": '+str(j)+' ,  "colrow": "'+str(i)+"_"+str(j)+'" ,  "generator": "Crop Rows Generator CLI" }, '
				tileCoords+='"geometry": { "type": "Polygon", '
				tileCoords+='"coordinates": [ [ [ '+str(coordinateX)+', '+str(coordinateY)+' ],'
				tileCoords+='[ '+str(coordinateX+tileSizeValue)+', '+str(coordinateY)+' ], '
				tileCoords+='[ '+str(coordinateX+tileSizeValue)+', '+str(coordinateY+(tileSizeValue*-1))+' ], '
				tileCoords+='[ '+str(coordinateX)+', '+str(coordinateY+(tileSizeValue*-1))+' ], '
				tileCoords+='[ '+str(coordinateX)+', '+str(coordinateY)+'] ] ] } },'

		polygonObjGeoJson+=' '+tileCoords[:-1]+' ] } }'
		geoJsonTileFileObject.write(polygonObjGeoJson)
		geoJsonTileFileObject.close()
		crutils.printLogMsg(crglobals.DONE_MSG+"Tile Index GeoJSON file: " + geoJsonTileFileName)

		endTime = time.time()
		elapsedTime = endTime - startTime
		crutils.printLogMsg(crglobals.SEPARATOR_MSG)
		# print total image generation time
		crutils.printLogMsg(crglobals.DONE_MSG+"Tiles Generation Process")
		crutils.printLogMsg(crglobals.DONEEND_MSG+"Total Processing Time: "+str(round(elapsedTime,2)) + " seconds")
		crutils.printLogMsg(crglobals.SEPARATOR_MSG)
		
		self.dirName = dirName
		self.nCols = nCols
		self.nRows = nRows

		return 1

	def getTilesGenerationGlobals(self):
		
		"""
		getTilesGenerationGlobals.
		
		:param self: (None).
		:returns dirName: tiles directory name.
		:returns nCols: num columns.
		:returns nRows: num rows.
		"""

		crutils.printLogMsg("%s %s" % (crglobals.DONE_MSG,"Getting Tiles Generation Globals"))
		return self.dirName , self.nCols , self.nRows

class CropRowsAnglesGenerator:

	anglesFoundArray = 0
	angleMean = 0
	angleSd = 0

	def anglesGeneration(self,cfgAnglesGenerator):

		"""
		anglesGeneration.
		
		:param cfgAnglesGenerator: (Array) angles generator config.
		:returns angle: (double) angle.
		"""

		tilesDirName=cfgAnglesGenerator[0]
		nCols=cfgAnglesGenerator[1]
		nRows=cfgAnglesGenerator[2]
		seedValue=cfgAnglesGenerator[3]
		seedSpanValue=cfgAnglesGenerator[4]

		anglesFoundArray = []

		cols = range(0,int(nCols),1)
		rows = range(0,int(nRows),1)

		nTiles = nCols * nRows

		totaltiles = nCols * nRows
		flagCurrent = 0

		filterTXTFileName = 'filtermaster_'+crglobals.PICNAME+"_"+str(nCols)+"_"+str(nRows)+"_"+str(nTiles)+"_"+crglobals.TILESENDNAME+".txt"
		filterTXTFileObject = open(os.path.join(tilesDirName,crglobals.VECTORDIR,filterTXTFileName),'w')
		filterTXTFileContent='"colrow" in ('
		filterTiles=""

		angleTXTFileName = 'anglemaster_'+crglobals.PICNAME+"_"+str(nCols)+"_"+str(nRows)+"_"+str(nTiles)+"_"+crglobals.TILESENDNAME+".txt"
		angleTXTFileObject = open(os.path.join(tilesDirName,crglobals.VECTORDIR,angleTXTFileName),'w')
		angleTXTFileObject.write('tile;angle\n')

		startTime = time.time()
		for i in cols:
			for j in rows:
				crutils.printLogMsg(crglobals.SEPARATOR_MSG)
				flagCurrent+=1
				flagStatus = int(((flagCurrent)/totaltiles)*100)
				crutils.printLogMsg(crglobals.START_MSG+"Processing Tile %s , %s - Status: %s %% " % (str(i), str(j) , str(flagStatus) ) )

				tileImageFileName = crglobals.PICNAME+'-'+crglobals.COLPREFIX+str(i)+'-'+crglobals.ROWPREFIX+str(j)+crglobals.JPG_EXT
				tileImageFileObject = os.path.join(tilesDirName,tileImageFileName)
				tileImageFileRasters = os.path.join(tilesDirName,crglobals.RASTERDIR,tileImageFileName)
				tileImageFileObjects = os.path.join(tilesDirName,crglobals.OBJDIR,tileImageFileName)

				try:

					originalRGBImage =crimgprep.readRGBImageByUrl(tileImageFileObject)

					###################################################################################
					#### preProcessingPipeline
					###################################################################################
					segmentedImage , rgbImageMasked , vegImage, _orgImage = crimgprep.preProcessingPipeline(originalRGBImage)

					cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.SEGMENTEDNAME+crglobals.JPG_EXT,segmentedImage)
					shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.SEGMENTEDNAME+crglobals.JPGX_EXT)
					crutils.printLogMsg(crglobals.OK_MSG+'Segmented Image generated')

					cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.MASKEDNAME+crglobals.JPG_EXT,rgbImageMasked)
					shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.MASKEDNAME+crglobals.JPGX_EXT)
					crutils.printLogMsg(crglobals.OK_MSG+'Masked Image generated')

					#if in segmentedImage there only 0 no segmentation objects was found

					if(np.max(segmentedImage) > 0):
						###################################################################################
						##### buildContours
						###################################################################################
						imgEdges, imgContours , contoursAll, contoursFiltred,angleFitMinAreaRect , meanAngleFitMinAreaRect , angleFitElipseContours , meanAngleFitElipseContours = crimgprep.buildContours(segmentedImage,seedValue,seedSpanValue)

						cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.EDGESNAME+crglobals.JPG_EXT,imgEdges)
						shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.EDGESNAME+crglobals.JPGX_EXT)
						crutils.printLogMsg(crglobals.OK_MSG+'Edges Image generated')
						cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.CONTOURSNAME+crglobals.JPG_EXT,imgContours)
						shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.CONTOURSNAME+crglobals.JPGX_EXT)
						crutils.printLogMsg(crglobals.OK_MSG+'Contours Image generated')

						crutils.printLogMsg(crglobals.DONE_MSG+'Mean Angle : %s Found' % (str(meanAngleFitElipseContours) ))

						anglesFoundArray.append(meanAngleFitElipseContours)
						
						###################################################################################
						##### drawContours
						###################################################################################
						imageClone = originalRGBImage.copy()

						composeImgContours , composeIimgSmallBoxes , composeImgGeoms = crimgprep.drawContours(imageClone, contoursAll)

						cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.COMPOSECONTNAME+crglobals.JPG_EXT,composeImgContours)
						shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.COMPOSECONTNAME+crglobals.JPGX_EXT)
						crutils.printLogMsg(crglobals.OK_MSG+'Compose Contours Image Generated')
						cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.COMPOSEBOXNAME+crglobals.JPG_EXT,composeIimgSmallBoxes)
						shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.COMPOSEBOXNAME+crglobals.JPGX_EXT)
						crutils.printLogMsg(crglobals.OK_MSG+'Compose Small Boxes Image Generated')
						cv2.imwrite(tileImageFileRasters[:-4]+'_'+crglobals.COMPOSEGEONAME+crglobals.JPG_EXT,composeImgGeoms)
						shutil.copy(tileImageFileObject[:-4]+crglobals.JPGX_EXT, tileImageFileRasters[:-4]+'_'+crglobals.COMPOSEGEONAME+crglobals.JPGX_EXT)
						crutils.printLogMsg(crglobals.OK_MSG+'Compose Geometries Image Generated')

						crutils.printLogMsg(crglobals.SEPARATOR_MSG)

						crutils.printLogMsg(crglobals.START_MSG+'Saving Contour file')
						np.save(tileImageFileObjects[:-4]+crglobals.NPYOBJ, contoursAll)
						crutils.printLogMsg(crglobals.OK_MSG+'Contour File Object Generated')

						filterTiles+="'"+str(i)+"_"+str(j)+"',"

						if(str(meanAngleFitElipseContours) != 'nan'):
							angleTiles="'"+str(i)+"_"+str(j)+"';"+str(meanAngleFitElipseContours)+"\n"
							angleTXTFileObject.write(angleTiles)

					else:
						crutils.printLogMsg(crglobals.NO_MSG+'No Segmentation Found for: %s' % (tileImageFileName))
				except:
					crutils.printLogMsg(crglobals.ERROR_MSG+'Fail: %s' % (tileImageFileObject))	

		filterTXTFileContent+=' '+filterTiles[:-1]+' )'
		filterTXTFileObject.write(filterTXTFileContent)
		filterTXTFileObject.close()
		crutils.printLogMsg(crglobals.SEPARATOR_MSG)
		crutils.printLogMsg(crglobals.DONE_MSG+"Filter Tile Index File: "+filterTXTFileName)
		angleTXTFileObject.close()
		crutils.printLogMsg(crglobals.DONE_MSG+"Angles Found Tile Index File: "+angleTXTFileName)
		crutils.printLogMsg(crglobals.SEPARATOR_MSG)

		endTime = time.time()
		elapsedTime = endTime - startTime
		crutils.printLogMsg(crglobals.SEPARATOR_MSG)
		# print total image generation time
		crutils.printLogMsg(crglobals.DONE_MSG+"Angles generation")
		crutils.printLogMsg(crglobals.DONEEND_MSG+"Total processing time: "+str(round(elapsedTime,2)) + " seconds")
		crutils.printLogMsg(crglobals.SEPARATOR_MSG)

		#statistical manipulation for angles found
		#anglesFoundArray[~np.isnan(anglesFoundArray)]
		angleMean = (np.nanmean(anglesFoundArray))
		angleSd = (np.nanstd(anglesFoundArray))

		if(np.isnan(angleMean)):
			crutils.printLogMsg(crglobals.ERROR_MSG+'Program terminated - Not enough angles found to perform the next step !\n')
			crutils.printLogMsg(crglobals.BANNER_END)
			sys.exit()
		else:
			crutils.printLogMsg(crglobals.CHECK_MSG+'Valid Angles')
		
		#return anglesFoundArray, angleMean , angleSd
		self.anglesFoundArray = anglesFoundArray
		self.angleMean = angleMean
		self.angleSd = angleSd
		return 1

	def getAnglesGeneratorGlobals(self):

		"""
		getAnglesGeneratorGlobals.
		
		:param self: (None).
		:returns anglesFoundArray: angles found array.
		:returns angleMean: angles mean.
		:returns angleSd: angles standard derivation.
		"""
		crutils.printLogMsg(crglobals.DONE_MSG+"Getting Angles Generation Globals")
		return self.anglesFoundArray , self.angleMean , self.angleSd

def generateCropRowsLinesAll(cfgLinesGenerator):
	
	"""
    generateCropRowsLinesAll.
       
    :param cfgLinesGenerator: (Array) config lines generator array.
	:returns None: None.
    """

	tilesDirName  = cfgLinesGenerator[0]
	meanAngleFitElipseContours = cfgLinesGenerator[1]
	pixelSizeValue = cfgLinesGenerator[2]
	imageExtentsValue = cfgLinesGenerator[3]
	epsgValue = cfgLinesGenerator[4]
	tileSizeValue = cfgLinesGenerator[5]
	nCols = int(cfgLinesGenerator[6])
	nRows = int(cfgLinesGenerator[7])
	
	cols = range(0,nCols,1)
	rows = range(0,nRows,1)

	totaltiles = nCols * nRows
	flagCurrent = 0

	startTime = time.time()
	for i in cols:
		for j in rows:
			crutils.printLogMsg(crglobals.SEPARATOR_MSG)
			flagCurrent+=1
			flagStatus = int(((flagCurrent)/totaltiles)*100)
			crutils.printLogMsg(crglobals.START_MSG+"Processing Tile %s , %s - Status: %s %% " % (str(i), str(j) , str(flagStatus) ) )
			
			fileNameValue = crglobals.PICNAME+'-'+crglobals.COLPREFIX+str(i)+'-'+crglobals.ROWPREFIX+str(j)+crglobals.NPYOBJ
			contourFile = os.path.join(tilesDirName,crglobals.OBJDIR,fileNameValue)

			dirName = tilesDirName

			#Masive Lines generation
			generateLinesFile(dirName, fileNameValue, contourFile, meanAngleFitElipseContours , pixelSizeValue , imageExtentsValue,epsgValue, i, j, tileSizeValue)
	
	endTime = time.time()
	elapsedTime = endTime - startTime
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	# print total lines generation time
	crutils.printLogMsg(crglobals.DONE_MSG+"GeoJSON Lines generation")
	crutils.printLogMsg(crglobals.DONEEND_MSG+"Total processing time: "+str(round(elapsedTime,2)) + " seconds")
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
			
	return 1

def generateLinesFile(dirName, fileNameValue, contourFile, meanAngleFitElipseContours , pixelSizeValue , imageExtentsValue,epsgValue, col, row, tileSizeValue):
	
	"""
	generateLinesFile.
	
	:param dirName: (String) dir name.
	:param fileNameValue: (String) file name.
	:param contourFile: (String) contour file name.
	:param meanAngleFitElipseContours: (double) mean angle from contours.
	:param pixelSizeValue: (int) pixel size.
	:param imageExtentsValue: (Array) image extents.
	:param epsgValue: (int) epsg code from spatial reference system.
	:param col: (int) column.
	:param row: (int) row.
	:param tileSizeValue: tile size.
	:returns None: None.
    """

	flagLineIdentificator = 0
	distanceLinearMaxArray = []

	cmPerPixel = (pixelSizeValue[0])*100
	pixelTile = (tileSizeValue*100)/cmPerPixel

	if(not os.path.isfile(contourFile)):
		crutils.printLogMsg(crglobals.NO_MSG+'Contour file not found *skip')
		return 0
	else:
		crutils.printLogMsg(crglobals.OK_MSG+'Contour file found ')
		pass
	
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	contoursAll = np.load(contourFile)

	tileAnglesArray = []
	if(meanAngleFitElipseContours==-1):
		crutils.printLogMsg('Search mean angle for tile')
		for cc in contoursAll:
			minAreaRectContour = cv2.minAreaRect(cc)
			boxContour = cv2.boxPoints(minAreaRectContour)
			angleMinAreaRect = cv2.minAreaRect(boxContour)[-1]
			tileAnglesArray.append(angleMinAreaRect)
		angleMean = (np.nanmean(tileAnglesArray))
		meanAngleFitElipseContours = angleMean
		crutils.printLogMsg(crglobals.OK_MSG+'Mean angle found: %s' % (meanAngleFitElipseContours))

	wktVectorLinesFile = open(os.path.join(dirName,crglobals.VECTORDIR,crglobals.OBJDIR,fileNameValue[:-4]+'_'+crglobals.VECTORLINES+crglobals.GEOJSON_EXT),'w')
	linesWKTObject='{"type": "FeatureCollection","crs": { "type": "name", "properties": '
	linesWKTObject+='{ "name": "urn:ogc:def:crs:EPSG::'+str(epsgValue)+'" } },"features":[ '
	linesCoords=""

	wktVectorPointsFile = open(os.path.join(dirName,crglobals.VECTORDIR,crglobals.OBJDIR,fileNameValue[:-4]+'_'+crglobals.VECTORPOINTS+crglobals.GEOJSON_EXT),'w')
	pointsWKTObject='{"type": "FeatureCollection","crs": { "type": "name", "properties": '
	pointsWKTObject+='{ "name": "urn:ogc:def:crs:EPSG::'+str(epsgValue)+'" } },"features":[ '
	pointsCoords=""

	flagLinesCounter=0
	centersArray=[]	
	centersLastArray=[]
	D =  1
	
	for cc in contoursAll:
	# find minimum area
		rectMin = cv2.minAreaRect(cc)
		# calculate coordinates of the minimum area rectangle
		boxMinRect = cv2.boxPoints(rectMin)
		x_,y_,w_,h_ = cv2.boundingRect(boxMinRect)
		boxMinRect = imutils.order_points(boxMinRect)
		(tl, tr, br, bl) = boxMinRect # (top left, top right, bottom right, bottom left)
		(tltrX, tltrY) = crutils.midPoint(tl, tr)  #PUNTO MEDIO ENTRE TOPLEFT Y TOPRIGHT
		(blbrX, blbrY) = crutils.midPoint(bl, br)  #PUNTO MEDIO ENTRE BOTTOMLEFT Y BOTTOMRIGHT
		(tlblX, tlblY) = crutils.midPoint(tl, bl) #PUNTO MEDIO ENTRE TOPLEFT Y BOTTOMLEFT
		(trbrX, trbrY) = crutils.midPoint(tr, br) #PUNTO MEDIO ENTRE TOPRIGHT Y BOTTOMRIGHT

		distanceTLTRtoBLBR = math.sqrt(((tltrX-blbrX)**2)+((tltrY-blbrY)**2))
		distanceTLBLtoTRBR = math.sqrt(((tlblX-trbrX)**2)+((tlblY-trbrY)**2))
		if(distanceTLTRtoBLBR >= distanceTLBLtoTRBR ):
			#cv2.line(cp_image, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),(0, 255, 126), 2)
			linearDistanceInMeters = distanceTLTRtoBLBR * cmPerPixel
		else:
			#cv2.line(cp_image, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),(0, 255, 0), 2)
			linearDistanceInMeters = distanceTLBLtoTRBR * cmPerPixel
		distanceLinearMaxArray.append(linearDistanceInMeters)

		(x,y),minEnclosingCircleRadius = cv2.minEnclosingCircle(cc)
		minEnclosingCenter = (int(x),int(y))
		thetaAngle = ((meanAngleFitElipseContours)*np.pi / 180)
		(x1p,y1p)=(minEnclosingCenter)
		(xcc,ycc) = crutils.midPoint(  ( tlblX ,  tlblY )  , ( trbrX ,  trbrY ) )    
		#(xcc,ycc),minEnclosingCircleRadius = cv2.minEnclosingCircle(box)

		#calculate differences - removing closest lines 
		if(flagLinesCounter%2==0):
			centersArray=[]	
			centersArray.append([xcc,ycc])
			#print('=0')
		else:
			centersLastArray=[]
			centersLastArray.append([xcc,ycc])
			#print('=)')

		#print(centersArray)
		#print(centersArray[0][0])
		if(len(centersLastArray) >=1):
			#print(centersLastArray)	
			#print(centersLastArray[0][0])
			dx= centersArray[0][0] - centersLastArray[0][0]
			dy = centersArray[0][1] - centersLastArray[0][1]
			D =  1
			D = np.sqrt(dx*dx+dy*dy)
			#print('DDD -->>' + str(D))

		rho = 1
		a = np.cos(thetaAngle)
		b = np.sin(thetaAngle)
		x0  = a*rho
		y0  = b*rho

		#print('--------------->>>'+ str(D))
		#x1p2 = x1p + 1000 * (-b)
		#y1p2 = y1p + 1000 * (a)
		#x2p2 = x1p - 1000 * (-b)
		#y2p2 = y1p - 1000 * (a)
		#cv2.line(cp_image, (int(x1p2), int(y1p2)) , (int(x2p2), int(y2p2)),(134, 241, 12), 2)
		#dlx=(x1p2/ (1/(cmPerPixel/100)))
		#dly=(y1p2/ (1/(cmPerPixel/100)))
		#drx=(x2p2/ (1/(cmPerPixel/100)))
		#dry=(y2p2/ (1/(cmPerPixel/100)))
		#tlblX_=(tlblX/ (1/(cmPerPixel/100)))
		#tlblY_=(tlblY/ (1/(cmPerPixel/100)))
		#trbrX_=(trbrX/ (1/(cmPerPixel/100)))
		#trbrY_=(trbrY/ (1/(cmPerPixel/100)))
		#yy = (tile_w  / (1/(cmPerPixel/100)))
		#trxx = (imageOriginValue[0])+(tile_w/(1/(cmPerPixel/100)))*(col-1)
		#tryy = (imageOriginValue[1])-(tile_w/(1/(cmPerPixel/100)))*(row)
		#print(pixelTile/(1/(pixelSizeValue[1])))

		x1C = xcc / (1/(pixelSizeValue[0])) + (imageExtentsValue[0]) + (tileSizeValue * (col-1))  #(pixelTile/(1/(pixelSizeValue[0])))*(col-1)
		y1C = ycc / (1/(pixelSizeValue[1])) + (imageExtentsValue[3]) + (-tileSizeValue * (row-1))  #(pixelTile/(1/(pixelSizeValue[1])))*(row-1)
		xc2 = xcc + (linearDistanceInMeters/4) * (-b)
		yc2 = ycc + (linearDistanceInMeters/4) * (a)
		#xc2 = xcc + (linearDistanceInMeters/4) * (-b)
		#yc2 = ycc + (linearDistanceInMeters/4) * (a)
		x2C = xc2 / (1/(pixelSizeValue[0])) + (imageExtentsValue[0]) + (tileSizeValue * (col-1))  #(pixelTile/(1/(pixelSizeValue[0])))*(col-1)
		y2C = yc2 / (1/(pixelSizeValue[1])) + (imageExtentsValue[3]) + (-tileSizeValue * (row-1))  #(pixelTile/(1/(pixelSizeValue[1])))*(row-1)

		#xmin,ymax,xmax,ymi
		#if(x1C< imageExtentsValue[0] ):
		#x2C = ((imageExtentsValue[0]) + (tileSizeValue * (col-1))) 
		#print(str(flagLinesCounter))
		#print(x1C)
		#print(imageExtentsValue[0])

		xc3 = xcc + (linearDistanceInMeters/4) * (b)
		yc3 = ycc + (linearDistanceInMeters/4) * (-a)
		x3C = xc3 / (1/(pixelSizeValue[0])) + (imageExtentsValue[0]) + (tileSizeValue * (col-1))  #(pixelTile/(1/(pixelSizeValue[0])))*(col-1)
		y3C = (yc3/ (1/(pixelSizeValue[1])) + (imageExtentsValue[3]) + (-tileSizeValue * (row-1)))  #(pixelTile/(1/(pixelSizeValue[1])))*(row-1)

		##CENTER LINE MINBOX
		#x1C = tlblX / (1/(pixelSizeValue[0])) + (imageExtentsValue[0]) + (tileSizeValue * (col-1))  #(pixelTile/(1/(pixelSizeValue[0])))*(col-1)
		#y1C = tlblY / (1/(pixelSizeValue[1])) + (imageExtentsValue[3]) + (-tileSizeValue * (row-1))  #(pixelTile/(1/(pixelSizeValue[1])))*(row-1)
		#x2C = trbrX / (1/(pixelSizeValue[0])) + (imageExtentsValue[0]) + (tileSizeValue * (col-1))  #(pixelTile/(1/(pixelSizeValue[0])))*(col-1)
		#y2C = trbrY / (1/(pixelSizeValue[1])) + (imageExtentsValue[3]) + (-tileSizeValue * (row-1))  #(pixelTile/(1/(pixelSizeValue[1])))*(row-1)
		###
		#print('is posble d ?'+str(D))
		#filter by min distance 
		if ( (linearDistanceInMeters > 1) ):
			#if(D>50 or D==1):
			if(1):
				linesCoords+='{ "type": "Feature", "properties": { "lcount": '+str(flagLinesCounter)+' ,  "len": '+str(linearDistanceInMeters)+'  , "d": '+str(D)+' , "col": '+str(col)+' , "row": '+str(row)+' , "generator": "Crop Rows Generator CLI" }, '
				linesCoords+='"geometry": { "type": "LineString", '
				linesCoords+='"coordinates": ['
				#print('LINESTRING('+str( 1.0* (dlx + trxx )) +' '+str( -1.0* (dly - tryy ) + yy ) +' , '+str( 1.0* (drx + trxx )) +' '+str( -1.0* (dry - tryy ) + yy  )+ ')')
				#linesCoords += '[ '+str( 1.0* (dlx + trxx )) +','+str( -1.0* (dly - tryy ) + yy ) +'] , [ '+str( 1.0* (drx + trxx )) +', '+str( -1.0* (dry - tryy ) + yy  )+ '] '
				#long lines
				#linesCoords += '[ '+str( 1.0* (dlx + trxx )) +','+str( -1.0* (dly - tryy ) + yy ) +'] , [ '+str( 1.0* (drx + trxx )) +', '+str( -1.0* (dry - tryy ) + yy  )+ '] '
				linesCoords += '[ '+str( 1.0* (x1C) ) +','+str( 1.0* (y1C) ) +'] , [ '+str( 1.0* (x2C)) +', '+str( 1.0* (y2C) )+ '] ' + ' , [ '+str( 1.0* (x3C)) +', '+str( 1.0* (y3C) )+ '] '
				linesCoords += ']}},'
				pointsCoords+='{ "type": "Feature", "properties": { "lcount": '+str(flagLinesCounter)+' , "typepoint": "mid"   , "col": '+str(col)+' , "row": '+str(row)+' }, '
				pointsCoords+='"geometry": { "type": "Point", '
				pointsCoords+='"coordinates": '
				pointsCoords += '[ '+str( 1.0* (x1C) ) +','+str( 1.0* (y1C) ) +'] }},'
				pointsCoords+='{ "type": "Feature", "properties": { "lcount": '+str(flagLinesCounter)+' , "typepoint": "ini"   , "col": '+str(col)+' , "row": '+str(row)+' }, '
				pointsCoords+='"geometry": { "type": "Point", '
				pointsCoords+='"coordinates": '
				pointsCoords += '[ '+str( 1.0* (x2C) ) +','+str( 1.0* (y2C) ) +'] }},'
				pointsCoords+='{ "type": "Feature", "properties": { "lcount": '+str(flagLinesCounter)+' , "typepoint": "end"   , "col": '+str(col)+' , "row": '+str(row)+' }, '
				pointsCoords+='"geometry": { "type": "Point", '
				pointsCoords+='"coordinates": '
				pointsCoords += '[ '+str( 1.0* (x3C) ) +','+str( 1.0* (y3C) ) +'] }},'
				
			flagLinesCounter+=1

	linesWKTObject+=' '+linesCoords[:-1]+'] }'
	wktVectorLinesFile.write(linesWKTObject)
	wktVectorLinesFile.close()
	crutils.printLogMsg(crglobals.OK_MSG+'Lines in GeoJSON file for col: %s row: %s generated' % ( str(col) , str(row)  ))
	pointsWKTObject+=' '+pointsCoords[:-1]+'] }'
	wktVectorPointsFile.write(pointsWKTObject)
	wktVectorPointsFile.close()
	crutils.printLogMsg(crglobals.OK_MSG+'Points in GeoJSON file for col: %s row: %s generated' % ( str(col) , str(row)  ))
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	
	return 1

#def saveResultXMLFile(resultXMLFile,resultXMLBuffer):
def saveResultXMLFile(resultingFiles):
	"""
    saveResultXMLFile.
       
    :param resultingFiles: (Array) crop rows results.
	:returns None: (none) none.
    """

	resultXMLFile = resultingFiles[0]
	resultXMLBuffer = resultingFiles[1]
	resultXMLExportFile = resultingFiles[2]
	resultXMLExportKML = resultingFiles[3]
	#metadata
	recordEPSG = resultingFiles[4]
	recordCandidateLines = resultingFiles[5]
	recordResultingLines = resultingFiles[6]
	recordMask = resultingFiles[7]

	headFromXmlFile,tailFromXmlFile = os.path.split(resultXMLFile)
	headn=os.path.normpath(headFromXmlFile).split(os.path.sep)
	headn.append(tailFromXmlFile)
	record=os.path.join(*headn[2:])

	headFromXmlFileBuf,tailFromXmlFileBuf = os.path.split(resultXMLBuffer)
	headnBuf=os.path.normpath(headFromXmlFileBuf).split(os.path.sep)
	headnBuf.append(tailFromXmlFileBuf)
	recordBuf=os.path.join(*headnBuf[2:])

	headFromXmlFileShp,tailFromXmlFileShp = os.path.split(resultXMLExportFile)
	headnShp=os.path.normpath(headFromXmlFileShp).split(os.path.sep)
	headnShp.append(tailFromXmlFileShp)
	recordShp=os.path.join(*headnShp[2:])

	headFromXmlFileKml,tailFromXmlFileKml = os.path.split(resultXMLExportKML)
	headnKml=os.path.normpath(headFromXmlFileKml).split(os.path.sep)
	headnKml.append(tailFromXmlFileKml)
	recordKml=os.path.join(*headnKml[2:])

	## saving tile geojson location
	tilepath=(headn[2:5])
	tilepath.append('tilemaster_'+headn[3]+'.geojson')
	recordtile=os.path.join(*tilepath)
	## saving croprows shapefile location
	fileNameXMLResultFile=os.path.join(*headn[:2])
	fileNameResultsXML =  os.path.join(fileNameXMLResultFile,'results_'+headn[2]+'.xml')
	root = cET.Element('croprows')
	filenameElement = cET.SubElement(root,'filename')
	metadataElement = cET.SubElement(root,'metadata')
	resultSubElement = cET.SubElement(filenameElement, 'result')
	resultSubElement.text = record
	resultSubElementBuf = cET.SubElement(filenameElement, 'buffer')
	resultSubElementBuf.text = recordBuf
	resultSubElementTile = cET.SubElement(filenameElement, 'tile')
	resultSubElementTile.text = recordtile
	resultSubElementShp = cET.SubElement(filenameElement, 'export')
	resultSubElementShp.text = recordShp
	resultSubElementKml = cET.SubElement(filenameElement, 'kml')
	resultSubElementKml.text = recordKml
	#store some metadata
	resultSubElementEPSG = cET.SubElement(metadataElement, 'epsg')
	resultSubElementEPSG.text = recordEPSG
	resultSubElementMask = cET.SubElement(metadataElement, 'vectormask')
	resultSubElementMask.text = recordMask
	resultSubElementCandidate = cET.SubElement(metadataElement, 'candidatelines')
	resultSubElementCandidate.text = recordCandidateLines
	resultSubElementResulting = cET.SubElement(metadataElement, 'resultinglines')
	resultSubElementResulting.text = recordResultingLines

	rootXMLString = cET.tostring(root)
	tree = ET.ElementTree(ET.fromstring(rootXMLString))
	tree.write(fileNameResultsXML, encoding="utf-8", xml_declaration=True)
	crutils.printLogMsg(crglobals.OK_MSG+'Save Result File XML: %s ' % ( fileNameResultsXML  ))
	return

def main():
	"croprows file utils module"
	crutils.printLogMsg('croprows_fileutils [ module loaded ]')

main()