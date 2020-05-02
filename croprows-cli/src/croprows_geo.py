"""
.. module:: croprows_geo.py
   :synopsis: Geospatial operations for croprows

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""
import croprows_globals as crglobals
import croprows_utils as crutils
from croprows_fileutils import saveResultXMLFile
import imutils_boundingrect as imboundrect

import pandas as pd
import geopandas as gpd
import json
import geojson
import fiona

from shapely.geometry import shape
from shapely.wkt import dumps, loads
from shapely.geometry import Point
from shapely.geometry.polygon import LineString, LinearRing, Polygon
from shapely.ops import nearest_points

import sys
import os
from os import walk
import time
import numpy as np
from numpy import zeros
import cv2
import math
import re
import itertools

from joblib import Parallel, delayed
import multiprocessing

from multiprocessing import active_children, Pool, freeze_support
from scipy.sparse.csgraph import connected_components

fiona.drvsupport.supported_drivers['kml'] = 'rw' # enable KML support which is disabled by default
fiona.drvsupport.supported_drivers['KML'] = 'rw' # enable KML support which is disabled by default




#inspired in shapely-extending-line-feature
#see: https://stackoverflow.com/questions/33159833/shapely-extending-line-feature?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
def getExtrapoledLine(startPoint,endPoint):

	"""
    getExtrapoledLine. Creates a line extrapoled in startPoint->endPoint direction
       
    :param startPoint: (Point) start point.
    :param endPoint: (Point) end point.
    :returns LineString: (LineString) line.
    """

	a = (startPoint[0]-crglobals.EXTRAPOL_RATIO*(endPoint[0]-startPoint[0]), startPoint[1]-crglobals.EXTRAPOL_RATIO*(endPoint[1]-startPoint[1]))
	b = (startPoint[0]+crglobals.EXTRAPOL_RATIO*(endPoint[0]-startPoint[0]), startPoint[1]+crglobals.EXTRAPOL_RATIO*(endPoint[1]-startPoint[1]))
	return LineString([a,b])


def extendAllLinesInParallel(tilesDirName,epsgValue,iCols,jRows,maskVectorFile,seedValue):
	
	"""
	extendAllLinesInParallel.
	
	:param tilesDirName: (String) tile directory name.
	:param epsgValue: (String) code for refrerence system.
	:param iCols: (int) current column.
	:param jRows: (int) current row.
	:param maskVectorFile: (String) mask file name.
	:param seedValue: (int) seed for crop rows orientation.
	:returns none: None.
    """

	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	crutils.printLogMsg(crglobals.WORKER_MSG+"extendAllLinesInParallel -> Processing Tile %s , %s " % (str(iCols), str(jRows)  ) )
	processName = multiprocessing.current_process().name
	crutils.printLogMsg(crglobals.START_MSG+'Process name: %s ' % (processName))
	crutils.printLogMsg(crglobals.START_MSG+"Parent processs: %s" % (str( os.getppid() )) )
	crutils.printLogMsg(crglobals.START_MSG+"Process id: %s" % (str( os.getpid() )) )

	crutils.printLogMsg(crglobals.CHECK_MSG+'tilesDirName: %s' % (tilesDirName))
	crutils.printLogMsg(crglobals.OK_MSG+'EPSG: %s' % (epsgValue))
	crutils.printLogMsg(crglobals.OK_MSG+'iCols: %s' % (iCols))
	crutils.printLogMsg(crglobals.OK_MSG+'jRows: %s' % (jRows))

	dirNameVectorResults = os.path.join(tilesDirName,crglobals.VECTORDIR)
	dirNameVectorObjResults = os.path.join(dirNameVectorResults,crglobals.OBJDIR)

	crutils.printLogMsg(crglobals.OK_MSG+'Vector dir: %s' % (dirNameVectorResults))
	crutils.printLogMsg(crglobals.OK_MSG+'Vector dir Obj: %s' % (dirNameVectorObjResults))
	crutils.printLogMsg(crglobals.OK_MSG+'Mask File: %s' % (maskVectorFile))

	boundsVectorFile = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str(iCols)+"-"+crglobals.ROWPREFIX+str(jRows)+crglobals.GEOJSON_EXT
	linesVectorFile = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str(iCols)+"-"+crglobals.ROWPREFIX+str(jRows)+"_"+crglobals.VECTORLINES+crglobals.GEOJSON_EXT
	crutils.printLogMsg(crglobals.OK_MSG+"Bounds File : %s" % (boundsVectorFile))
	crutils.printLogMsg(crglobals.OK_MSG+"Lines File: %s" % (linesVectorFile))

	crutils.printLogMsg(crglobals.CHECK_MSG+'File %s is correct !' % (linesVectorFile) )

	extendLinesGeom(iCols,jRows,epsgValue,dirNameVectorResults,dirNameVectorObjResults,boundsVectorFile,linesVectorFile,maskVectorFile,seedValue)
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)

	return 1


def extendLinesGeom(col,row,epsgValue,dirNameVectorResults,dirNameVectorObjResults,boundsVectorFile,linesVectorFile,maskVectorFile,seedValue):

	"""
	extendLinesGeom.

	:param col: (int) current column.
	:param row: (int) current row.
	:param dirNameVectorResults: (String) vector dir path.
	:param boundsVectorFile: (String) bounds file.
	:param linesVectorFile: (String) lines file.
	:param maskVectorFile: (String) mask file.
	:returns none: (None) nothing.
	"""

	linesExtendedFileName = crglobals.PICNAME+"-"+crglobals.COLPREFIX+str(col)+"-"+crglobals.ROWPREFIX+str(row)+"_"+crglobals.VECTORLINES+"_ext.shp"
	
	#os.path.join(
	if (os.path.exists(  os.path.join(dirNameVectorResults, boundsVectorFile) )) and (os.path.exists( os.path.join(dirNameVectorObjResults,linesVectorFile) )) :
		crutils.printLogMsg(crglobals.CHECK_MSG+'Exists: %s' % (os.path.join(dirNameVectorResults,boundsVectorFile)))
		crutils.printLogMsg(crglobals.CHECK_MSG+'Exists: %s' % (os.path.join(dirNameVectorObjResults,linesVectorFile)))
		boxGeoDataFrame = gpd.GeoDataFrame.from_file(os.path.join(dirNameVectorResults,boundsVectorFile))#dirNameVectorResults+"/"+boundsVectorFile)
		try:
			linesGeoDataFrame = gpd.GeoDataFrame.from_file(os.path.join(dirNameVectorObjResults,linesVectorFile))#dirNameVectorObjResults+"/"+linesVectorFile)
			maskGeoDataFrame = gpd.GeoDataFrame.from_file(maskVectorFile)
			extendProcessing(boxGeoDataFrame,linesGeoDataFrame,epsgValue,dirNameVectorObjResults,linesExtendedFileName,maskGeoDataFrame,col,row,seedValue)
		except KeyError as exception:
			crutils.printLogMsg('Bounds file: %s' % (boundsVectorFile))
			crutils.printLogMsg('Lines file: %s' % (linesVectorFile))
			crutils.printLogMsg(crglobals.FAIL_MSG+'Geometry not found')
	else:
		crutils.printLogMsg(crglobals.FAIL_MSG+'Lines or bounds file does not exist %s' % (os.path.join(dirNameVectorObjResults,linesVectorFile)))

	return 1

def extendProcessing(boxGeoDataFrame,linesGeoDataFrame,epsgValue,dirNameVectorObjResults,linesExtendedFileName,vectorMask,col,row,seedValue):

	"""
	extendProcessing.
	
	:param boxGeoDataFrame: (Box) box
	:param linesGeoDataFrame: (int) lines
	:param epsgValue: (int) spatial reference system
	:param dirNameVectorObjResults: (String) vector objects folder
	:param linesExtendedFileName: (String) lines extended file.
	:param seedValue: (int) seed for crop rows orientation.
	:returns none: None.
    """
	crsEpsgId = {'init': 'epsg:'+str(epsgValue)}

	longLinesArray		=	[]
	idLongLinesArray		=	[]
	cuttedLineArray 	= 	[]
	newidcutedline 	= 	[]
	newobjdistances = 	[]
	distanceLinear 		= 	[]
	index = []
	
	flagCounter = 0

	externalPoint = Point( (0,0) )

	#Extrapolate lines
	for x in range (0 , len(linesGeoDataFrame.geometry)):
	    linea_bx= (list(linesGeoDataFrame.geometry[x].coords))
	    extrapoledLine = getExtrapoledLine(*linea_bx[-2:])
	    idLongLinesArray.append(x)
	    longLinesArray.append(extrapoledLine)
	        
	dataFrameLongLines = pd.DataFrame({'id': idLongLinesArray})
	longLinesGeoDataFrame=gpd.GeoDataFrame(dataFrameLongLines, crs=crsEpsgId, geometry=longLinesArray)
	crutils.printLogMsg(crglobals.DONE_MSG+'Generated long lines !')

	dataFrameLineCuttedByBox=(longLinesGeoDataFrame.intersection(boxGeoDataFrame.geometry.iloc[0]))
	geoDataFrameLinesCuttedByBox=gpd.GeoDataFrame(crs=crsEpsgId, geometry=dataFrameLineCuttedByBox)
	crutils.printLogMsg(crglobals.DONE_MSG+'Cut long lines by bounds !')

	#############################################
	### TEST #change 06-06-2018
	#Get the convex hull lines
	convexHullFromMask = vectorMask.convex_hull.iloc[0]
	x, y = convexHullFromMask.exterior.xy
	pointsConvexHullFromMaskArray = np.array(list(zip(x,y)))
	minBBoxRect= imboundrect.minimum_bounding_rectangle(pointsConvexHullFromMaskArray)
	polygonOMBB = Polygon([minBBoxRect[0], minBBoxRect[1], minBBoxRect[2] , minBBoxRect[3]])
	#cut lines by ombb
	#longLinesGeoDataFrame
	dataFrameLineCuttedByMask=(geoDataFrameLinesCuttedByBox.intersection(polygonOMBB))
	#############################################

	#change 06-06-2018
	#dataFrameLineCuttedByMask=(geoDataFrameLinesCuttedByBox.intersection(vectorMask.geometry.iloc[0]))
	geoDataFrameLineCuttedByMask=gpd.GeoDataFrame(crs=crsEpsgId, geometry=dataFrameLineCuttedByMask)
	crutils.printLogMsg(crglobals.DONE_MSG+'Line clipping by mask!')

	#################################
	#if cutlinedk[0].length > 0:
	#	angle=crutils.getAzimuth( (cutlinedk[0].coords[0][0]) , (cutlinedk[0].coords[0][1]) , (cutlinedk[0].coords[1][0]) ,  (cutlinedk[0].coords[1][1]) )
	#	anglep =(angle+270)
	#	xp = (np.min(box.geometry.bounds.minx)) + np.sin(np.deg2rad(anglep)) * 10
	#	yp = (np.max(box.geometry.bounds.maxy)) + np.cos(np.deg2rad(anglep)) * 10
	#	externalPoint = Point( ( xp,yp ) )
	#################################
		#print(str(anglep))
		#print(cutlinedk[0].centroid.x)
		#print(cutlinedk[0].centroid.y)
		#print('--------------ANGULO -------------------')
		#print(angle)
		#print('--------------ANGULO PERPEN-------------------')
		#xp = (cutlinedk[0].centroid.x) + np.sin(np.deg2rad(anglep)) * 20
		#yp = (cutlinedk[0].centroid.y) + np.cos(np.deg2rad(anglep)) * 20
		#print( 'POINT( %s  %s )' % ( xp,yp))

	#####
	#TODO: Order id by spatial criteria
	#####

	#line1 = LineString([(np.min(box.geometry.bounds.minx), np.min(box.geometry.bounds.miny)), 
    #               (np.max(box.geometry.bounds.maxx), np.min(box.geometry.bounds.miny))])
	
	crutils.printLogMsg(crglobals.DONE_MSG+'Calculate distance by seed criteria : %s ' % (str(seedValue) ))

	projectDistance = 100
	
	if(seedValue==1):
		pnt0Calc = (LineString([(np.min(boxGeoDataFrame.geometry.bounds.minx), np.max(boxGeoDataFrame.geometry.bounds.maxy)), (np.max(boxGeoDataFrame.geometry.bounds.maxx), np.max(boxGeoDataFrame.geometry.bounds.maxy))])).centroid
	elif(seedValue==2):
		pnt0Calc = (LineString([(np.min(boxGeoDataFrame.geometry.bounds.minx), np.max(boxGeoDataFrame.geometry.bounds.maxy)), (np.min(boxGeoDataFrame.geometry.bounds.minx), np.min(boxGeoDataFrame.geometry.bounds.miny))])).centroid
	elif(seedValue==3):
		if dataFrameLineCuttedByMask[0].length > 0:
			angle=crutils.getAzimuth( (dataFrameLineCuttedByMask[0].coords[0][0]) , (dataFrameLineCuttedByMask[0].coords[0][1]) , (dataFrameLineCuttedByMask[0].coords[1][0]) ,  (dataFrameLineCuttedByMask[0].coords[1][1]) )
			anglep =(angle+270)
			xp = (np.min(boxGeoDataFrame.geometry.bounds.minx)) + np.sin(np.deg2rad(anglep)) * projectDistance
			yp = (np.max(boxGeoDataFrame.geometry.bounds.maxy)) + np.cos(np.deg2rad(anglep)) * projectDistance
			externalPoint = Point( ( xp,yp ) )

		pnt0Calc = externalPoint
		#Point((np.min(boxGeoDataFrame.geometry.bounds.minx), np.max(boxGeoDataFrame.geometry.bounds.maxy)))
	elif(seedValue==4):
		if dataFrameLineCuttedByMask[0].length > 0:
			angle=crutils.getAzimuth( (dataFrameLineCuttedByMask[0].coords[0][0]) , (dataFrameLineCuttedByMask[0].coords[0][1]) , (dataFrameLineCuttedByMask[0].coords[1][0]) ,  (dataFrameLineCuttedByMask[0].coords[1][1]) )
			anglep =(angle+270)
			xp = (np.max(boxGeoDataFrame.geometry.bounds.maxx)) + np.sin(np.deg2rad(anglep)) * projectDistance
			yp = (np.max(boxGeoDataFrame.geometry.bounds.maxy)) + np.cos(np.deg2rad(anglep)) * projectDistance
			externalPoint = Point( ( xp,yp ) )

		pnt0Calc = externalPoint
		#pnt0Calc = Point((np.max(boxGeoDataFrame.geometry.bounds.maxx), np.max(boxGeoDataFrame.geometry.bounds.maxy)))
	
	boxminxmaypoint = pnt0Calc

	crutils.printLogMsg(crglobals.DONE_MSG+'%s chosen for distance calculation' % (boxminxmaypoint) )

	for x in range (0 , len(geoDataFrameLineCuttedByMask.geometry)):
		if geoDataFrameLineCuttedByMask.geometry.geom_type[x] == 'LineString':
			if(len(list(geoDataFrameLineCuttedByMask.geometry[x].coords)))==2:
				linea_bx= LineString(list(geoDataFrameLineCuttedByMask.geometry[x].coords))
				if(linea_bx.length > crglobals.MINLINEDISTANCE ):
					index.append(flagCounter)
					flagCounter +=1
					#newidcutedline.append(x)
					cuttedLineArray.append(linea_bx)
					distanceLinear.append(linea_bx.length)
					#print('centroid')
					#print(linea_bx.centroid)
					distanceplin = boxminxmaypoint.distance(linea_bx.centroid)
					newobjdistances.append(distanceplin)
				
	sortedDistance = np.argsort(newobjdistances).astype('int')
	idByGeo = [x for _,x in sorted(zip(sortedDistance,index))]

	#Sort Distances
	newObjDistancesSorted= np.sort(newobjdistances)
	#Removing Adjacents and lines duplicates
	newObjDistancesSorted = crutils.removeAdjacentsInArray(newObjDistancesSorted)

	crutils.printLogMsg(crglobals.DONE_MSG+'Removed adjacents and duplicate lines !')
	
	#print('distances: %s ' % (newobjdistances) )
	#print('---------->distances kk: %s ' % (newObjDistancesSorted) )
	
	##Removing Closing Lines
	pairsdistances = zip([0]+newObjDistancesSorted, newObjDistancesSorted)
	distancesFiltered = [pair[1] for pair in pairsdistances if abs(pair[0]-pair[1]) >= crglobals.MINCROPROWDISTANCE ]
	#distancesFiltered = [pair[1] for pair in pairsdistances if abs(pair[0]-pair[1]) >= crglobals.MINCROPROWDISTANCE and abs(pair[0]-pair[1]) <= crglobals.MAXCROPROWDISTANCE ]
	
	#remove
	#add 3-9-2018
	#pairsdistances2 = zip([0]+distancesFiltered, distancesFiltered)
	#distancesFiltered = [pair2[1] for pair2 in pairsdistances2 if abs(pair2[0]-pair2[1]) <=  crglobals.MAXCROPROWDISTANCE ]
	#distancesFiltered.append(newObjDistancesSorted[len(newObjDistancesSorted)])

	crutils.printLogMsg(crglobals.DONE_MSG+'Removed closing lines by proximity MIN : %s units ' % ( str(crglobals.MINCROPROWDISTANCE)) )
	#crutils.printLogMsg(crglobals.DONE_MSG+'Removed closing lines by proximity MAX : %s units ' % ( str(crglobals.MAXCROPROWDISTANCE)) )

	#print('new x: %s ' % (distancesFiltered) )
	getIndexes = lambda x, xs: [i for (y, i) in zip(xs, range(len(xs))) if x == y]

	#look for 
	k=[]
	flagCounter3=0
	for x in distancesFiltered:
		#print(distancesFiltered[i])
		#print(getIndexes(distancesFiltered[i],newobjdistances))
		k.append(getIndexes(distancesFiltered[flagCounter3],newobjdistances)[0])
		flagCounter3=flagCounter3+1

	#Reindex lines filtered
	index2 = []
	flagCounter2 = 0
	m=[]
	j=0
	for x in k:
		m.append(cuttedLineArray[k[j]])
		index2.append(flagCounter2)
		flagCounter2 +=1
		j=j+1
	
	sortdistance2 = np.argsort(distancesFiltered).astype('int')
	idByGeo2 = [x for _,x in sorted(zip(sortdistance2,index2))]

	crutils.printLogMsg(crglobals.DONE_MSG+'Re-indexing candidate lines !')

	#Fix distances substracting projectDistance
	arrayDistances = np.array(distancesFiltered)
	fixdist = arrayDistances - projectDistance
	crutils.printLogMsg(crglobals.DONE_MSG+'Distances fixed !')

	dataFrameFixedLines = pd.DataFrame({ 'id': k ,  'col': str(col) , 'row': str(row) , 'colrow': str(col)+'_'+str(row)  })
	geoDataFrameFixedLines=gpd.GeoDataFrame(dataFrameFixedLines, crs=crsEpsgId, geometry=m)		
	geoDataFrameFixedLines.dropna()
	
	extfile =  os.path.join(dirNameVectorObjResults,linesExtendedFileName)#dirNameVectorObjResults+'/'+linesExtendedFileName

	if(len(geoDataFrameFixedLines.values)>0):
		#ddkfhmm.to_file(driver = 'ESRI Shapefile', filename=str(extfile))
		crutils.printLogMsg(crglobals.DONE_MSG+'Writing file line extended and clipped: %s ' % (extfile))
		geoDataFrameFixedLines.to_file(driver = 'ESRI Shapefile', filename=str(extfile))
	else:
		crutils.printLogMsg(crglobals.FAIL_MSG+'Invalid geometry skip file writing: %s ' % (extfile))

	return 1
	#"[Done] Lines extended and clipped by mask"

def mergeAllLines(dirPathLines,epsgValue):

	"""
    mergeAllLines.
       
    :param dirPathLines: (String) path.
	:param epsgValue: (int) epsg code.
    :returns none: None.
    """

	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	lineask = []
	for file in os.listdir(dirPathLines):
		if file.endswith(".shp"):
			if file.startswith("mosaic"):
				filesm = os.path.join(dirPathLines, file)
				crutils.printLogMsg(crglobals.OK_MSG+'Reading file: %s ' % (filesm))
				lineask.append( gpd.GeoDataFrame.from_file(filesm) )

	mergedLinesArray=[]
	a=0
	for i in lineask:
		mergedLinesArray.append(lineask[a])
		a+=1
	
	result = pd.concat(mergedLinesArray,axis=0)
	
	result.to_file(driver = 'ESRI Shapefile', filename= os.path.join(dirPathLines,'merged_lines.shp'))
	crutils.printLogMsg(crglobals.DONE_MSG+'Save merged lines !!')

	crutils.printLogMsg(crglobals.START_MSG+'Merge all Points from merged lines')
	
	crsEpsgId = {'init': 'epsg:'+str(epsgValue)}
	col = result.columns.tolist()[:-1]
	#[0:5]
	#print(col)
	nodes = gpd.GeoDataFrame(crs=crsEpsgId, columns=col)
	# extraction of nodes and attribute values nouveau GeoDataFrame
	for index, row in result.iterrows():
		for pt in list(row['geometry'].coords):
			#nodes = nodes.append({'col': int(row['col']), 'row': int(row['row']),  'distance':row['distance'],'id':row['id'], 'geometry':Point(pt) },ignore_index=True)
			nodes = nodes.append({'col': str(row['col']), 'row': str(row['row']), 'colrow': str(row['col'])+'_'+str(row['row']) , 'id':str(row['id']), 'geometry':Point(pt) },ignore_index=True)
	nodes.head(5)

	nodes.to_file(driver = 'ESRI Shapefile', filename= os.path.join(dirPathLines,'merged_points.shp'))
	crutils.printLogMsg(crglobals.DONE_MSG+'Save merged points !!')

	return 1

def mergeAllPoints(dirPathLines,epsgValue):
	
	"""
	mergeAllPoints.
	
	:param dirPathLines: (text) path lines directory.
	:param epsgValue: (int) epsg code.
	:returns None: (None).
	"""

	#mosaic-cl_17-rw_4_points
	crsEpsgId = {'init': 'epsg:'+str(epsgValue)}

	mergePointsArray = []
	for file in os.listdir(dirPathLines):
		if file.endswith(".geojson"):
			if file.startswith("mosaic"):
				if file.find("points") != -1:
					filesm = os.path.join(dirPathLines, file)
					#print(filesm)
					try:
						mergePointsArray.append( gpd.GeoDataFrame.from_file(filesm) )
					except KeyError:
						crutils.printLogMsg('In file: %s' % (filesm))
						crutils.printLogMsg(crglobals.FAIL_MSG+'Points file without geometry column !')


	#print(mergePointsArray)
	mergedLinesArray=[]
	a=0
	for i in mergePointsArray:
		mergedLinesArray.append(mergePointsArray[a])
		a+=1
	
	result = pd.concat(mergedLinesArray,axis=0)
	
	result.to_file(driver = 'ESRI Shapefile', filename= os.path.join(dirPathLines,'merged_rawpoints.shp'))
	crutils.printLogMsg(crglobals.DONE_MSG+'Save merged raw points !!')

	return 1



def extendAllMergedLines(dirPathLines,vectorMask,epsgValue):

	"""
    extendAllMergedLines.
       
    :param dirPathLines: (text) path
	:param vectorMask: (text) path
	:param epsgValue: (text) epsg value
    :returns: OpenCV version.
    """

	crsEpsgId = {'init': 'epsg:'+str(epsgValue)}

	crutils.printLogMsg(crglobals.OK_MSG+'Path Lines: %s' % (dirPathLines))
	crutils.printLogMsg(crglobals.OK_MSG+'Mask: %s' % (vectorMask))
	crutils.printLogMsg(crglobals.OK_MSG+'EPSG: %s' % (epsgValue))

	#input merged line file
	fileNameMergedLines='merged_lines.shp'
	mergedLinesGeoDataFrame = gpd.GeoDataFrame.from_file(os.path.join(dirPathLines,fileNameMergedLines))#dirPathLines+'/'+fileNameMergedLines)
	#input mask polygon file
	boundsMaskGeoDataFrame = gpd.GeoDataFrame.from_file(vectorMask)

	longLinesArray=[]
	idLongLinesArray=[]
	for x in range (0 , len(mergedLinesGeoDataFrame.geometry)):
		linea_bx= (list(mergedLinesGeoDataFrame.geometry[x].coords))
		extrapoledLine = getExtrapoledLine(*linea_bx[-2:])
		idLongLinesArray.append(x)
		longLinesArray.append(extrapoledLine)

	dataFrameLongLines = pd.DataFrame({'id': idLongLinesArray})
	longLinesGeoDataFrame=gpd.GeoDataFrame(dataFrameLongLines, crs=crsEpsgId, geometry=longLinesArray)
	longLinesFileName= os.path.join(dirPathLines,'merged_lines_long.shp')#dirPathLines+'/'+'merged_lines_long.shp'
	longLinesGeoDataFrame.to_file(driver = 'ESRI Shapefile', filename=longLinesFileName)
	crutils.printLogMsg(crglobals.DONE_MSG+'Generated long lines !')

	#######################################################################################
	#Get the convex hull lines
	convexHullFromBoundsMask = boundsMaskGeoDataFrame.convex_hull.iloc[0]
	x, y = convexHullFromBoundsMask.exterior.xy
	pointsConvexHullFromBoundsMaskArray = np.array(list(zip(x,y)))
	minBBoxRect= imboundrect.minimum_bounding_rectangle(pointsConvexHullFromBoundsMaskArray)
	polygonOMBB = Polygon([minBBoxRect[0], minBBoxRect[1], minBBoxRect[2] , minBBoxRect[3]])
	#######################################################################################
	#cut lines by ombb
	#update applying buffer. it fix some strange bug at some corner lines
	geoDataFrameLineCuttedByBoxBuffer=(longLinesGeoDataFrame.intersection(polygonOMBB.buffer(20) ))
	dataFrameLineCuttedByBoxDf = pd.DataFrame({ 'id': idLongLinesArray, 'len': geoDataFrameLineCuttedByBoxBuffer.length  })
	geoDataFrameLinesCuttedByBox=gpd.GeoDataFrame(dataFrameLineCuttedByBoxDf, crs=crsEpsgId, geometry=geoDataFrameLineCuttedByBoxBuffer)
	mergedLinesCuttedByOMBBPolygonFile= os.path.join(dirPathLines,'merged_lines_long_cut_ombb.shp')#dirPathLines+'/'+'merged_lines_long_cut_ombb.shp'
	geoDataFrameLinesCuttedByBox.to_file(driver = 'ESRI Shapefile', filename=mergedLinesCuttedByOMBBPolygonFile)
	crutils.printLogMsg(crglobals.DONE_MSG+'Cut long lines by OMBB bounds !')

	#######################################################################################
	projectDistance = 1
	#enumerate lines in spatial order
	angle=crutils.getAzimuth( (geoDataFrameLinesCuttedByBox.geometry[0].coords[0][0]) , (geoDataFrameLinesCuttedByBox.geometry[0].coords[0][1]) , (geoDataFrameLinesCuttedByBox.geometry[0].coords[1][0]) , (geoDataFrameLinesCuttedByBox.geometry[0].coords[1][1]) )
	anglep =(angle+270)
	#search for the closest geometry line to temporal point
	temporalXpoint = (geoDataFrameLinesCuttedByBox.geometry[0].centroid.x) + np.sin(np.deg2rad(anglep)) * 5000
	temporalYpoint = (geoDataFrameLinesCuttedByBox.geometry[0].centroid.y) + np.cos(np.deg2rad(anglep)) * 5000
	temporalExternalPoint = Point( ( temporalXpoint,temporalYpoint ) )
	crutils.printLogMsg(crglobals.DONE_MSG+'Generate a Temporal Point')
	#print(temporalExternalPoint)
	tmpLineDistance=[]
	for i in range(len(geoDataFrameLinesCuttedByBox)):
		distanceCalculated=(temporalExternalPoint.distance(geoDataFrameLinesCuttedByBox.geometry[i].centroid))
		tmpLineDistance.append(distanceCalculated)
		#print("i: %s -> distanceCalculated: %s -> %s" % (str(i), str(distanceCalculated) , str(geoDataFrameLinesCuttedByBox.geometry[i])   ))
	minelem=np.argmin(tmpLineDistance)
	crutils.printLogMsg(crglobals.DONE_MSG+"Found a closest line id: %s" % ( str(minelem) ) )
	#######################################################################################
	#Calc Distances using the closest line found
	xp = (geoDataFrameLinesCuttedByBox.geometry[minelem].centroid.x) + np.sin(np.deg2rad(anglep)) * projectDistance
	yp = (geoDataFrameLinesCuttedByBox.geometry[minelem].centroid.y) + np.cos(np.deg2rad(anglep)) * projectDistance
	externalPoint = Point( ( xp,yp ) )
	#print(externalPoint)

	geoDistance = []
	index = []

	for i in range(len(geoDataFrameLinesCuttedByBox)):
		#print('-> %s' % ( str( i)))
		distanceCalculated=(externalPoint.distance(geoDataFrameLinesCuttedByBox.geometry[i].centroid))
		geoDistance.append(distanceCalculated)
		#print(distanceCalculated)
		index.append(i)

	dataFrameLineCuttedByBoxBuffer = pd.DataFrame({ 'len': geoDataFrameLineCuttedByBoxBuffer.length , 'geo_dist': geoDistance , 'idx': index  })
	geoDataFrameLinesCuttedByBox=gpd.GeoDataFrame(dataFrameLineCuttedByBoxBuffer, crs=crsEpsgId, geometry=geoDataFrameLineCuttedByBoxBuffer)
	
	mergedLongLinesCuttedByOMBwDistFileName= os.path.join(dirPathLines,'merged_lines_long_cut_ombb_wdist.shp')#dirPathLines+'/'+'merged_lines_long_cut_ombb_wdist.shp'
	geoDataFrameLinesCuttedByBox.to_file(driver = 'ESRI Shapefile', filename=mergedLongLinesCuttedByOMBwDistFileName)

	#######################################################################################
	#######################################################################################
	############## FILTERING LINES LOOKING FOR CANDIDATES #################################
	#######################################################################################
	#######################################################################################


	sortedDistance = np.argsort(geoDistance).astype('int')
	idByGeo = [x for _,x in sorted(zip(sortedDistance,index))]

	newObjDistancesSorted= np.sort(geoDistance)

	#Removing Adjacents and lines duplicates
	newObjDistancesSorted = crutils.removeAdjacentsInArray(newObjDistancesSorted)

	#print('====== new distances sorted =====')
	#print(newObjDistancesSorted)
	crutils.printLogMsg( crglobals.DONE_MSG+'Candidate lines: %s ' %  str(len(newObjDistancesSorted)) )

	##Removing Closing Lines
	#pairsdistances = zip([0]+newObjDistancesSorted, newObjDistancesSorted)

	#TODO: distancesFiltered
	#distancesFiltered = [pair[1] for pair in pairsdistances if abs(pair[0]-pair[1]) >=0.5 ]
	###########################################
	## OTRO APPROACH TO FIND DISTANCES

	groups, current_group, first = [], [], newObjDistancesSorted[0]
	for item in newObjDistancesSorted:
		# Check if this element falls under the current group
		if item - first <= 1.3:
			current_group.append(item)
		else:
		# If it doesn't, create a new group and add old to the result
			groups.append(current_group[:])
			current_group, first = [item], item
		# Add the last group which was being gathered to the result
	groups.append(current_group[:])
	distancesFiltered=[np.max(item) for item in groups]

	#iter 1 removing proximal lines
	pairsdistances2 = zip([0]+distancesFiltered, distancesFiltered)
	distancesFiltered = [pair[1] for pair in pairsdistances2 if abs(pair[0]-pair[1]) >= 0.4 ]

	#iter 2 removing proximal lines
	pairsdistances3 = zip([0]+distancesFiltered, distancesFiltered)
	distancesFiltered = [pair[1] for pair in pairsdistances3 if abs(pair[0]-pair[1]) >= 0.9 ]  #>=0.8  -preff: 0.9



	######################################3
	#print('====== distances filtered =====')
	#print(distancesFiltered)

	crutils.printLogMsg( crglobals.DONE_MSG+'Resulting lines: %s ' %  str(len(distancesFiltered)) )

	#TODO: final 

	#cut final lines by mask
	dataFrameCandidateLines=(geoDataFrameLinesCuttedByBox.intersection(boundsMaskGeoDataFrame.geometry.iloc[0]))
	
	candidateLinesFileName= os.path.join(dirPathLines,'candidate_lines.shp')#dirPathLines+'/'+'candidate_lines.shp'

	dataFrameLineCuttedByMask = pd.DataFrame({ 'distance': dataFrameCandidateLines.length , 'geo_dist': geoDistance , 'idx': index })
	
	geoDataFrameLineCuttedByMask=gpd.GeoDataFrame(dataFrameLineCuttedByMask, crs=crsEpsgId, geometry=dataFrameCandidateLines)
	geoDataFrameLineCuttedByMask.to_file(driver = 'ESRI Shapefile', filename=candidateLinesFileName)


	#####################################
	## NEW CROPROWS - GEOMETRY SEARCH
	#####################################

	#save candidateLinesbuffer
	candidateLinesBufferFileName= os.path.join(dirPathLines,'candidate_lines_buffer.shp')
	candidateLinesBuffer = geoDataFrameLineCuttedByMask.buffer(0.3)
	s = candidateLinesBuffer
	
	#ADDING FEATURE 3-9-2018
	#DISOLVE OVERLAPPING BUFFER POLYGONS
	#https://gis.stackexchange.com/questions/271733/geopandas-dissolve-overlapping-polygons/271735
	overlap_matrix = s.apply(lambda x: s.overlaps(x)).values.astype(int)
	n, ids = connected_components(overlap_matrix)
	df = gpd.GeoDataFrame({'geometry': s, 'group': ids},crs=crsEpsgId)
	res = df.dissolve(by='group')
	res.to_file(driver = 'ESRI Shapefile', filename=candidateLinesBufferFileName)

	candidateLinesBufferCentroidFileName= os.path.join(dirPathLines,'candidate_lines_buffer_centroid.shp')
	points = res.copy()
	points.geometry = res['geometry'].centroid
	points.crs =res.crs
	points.head()
	points.to_file(driver = 'ESRI Shapefile', filename=candidateLinesBufferCentroidFileName)
	
	df_lines = dataFrameCandidateLines.geometry
	df_points = points.geometry
	#print(len(df_points))
	#print(len(df_lines))

	idClosestLineArr = [] 
	#find the closest candidate line to point
	for x in range(0, len(df_points) ) :	
		minDistancePointLine = df_lines.distance(df_points[x]).min() 
		allDistanceToLines = df_lines.distance(df_points[x])
		idClosestLine = np.where(allDistanceToLines==minDistancePointLine)[0]
		idClosestLineArr.append(idClosestLine[0])
		#print('centroid point: %s - id closest line: ' % (str(x)) , (str(idClosestLine))   )
	
	#print(idClosestLineArr)
	selcr = []
	for x in range(0, len(df_lines) ) :
		selcr = df_lines[ idClosestLineArr ]

	crf =0
	geoidcr = []
	croprowLength =[]

	for y in range(0,len(selcr)):
		#print(selcr.geometry.iloc[y])
		#print(selcr.geometry.iloc[y].length)
		croprowLength.append( selcr.geometry.iloc[y].length )
		geoidcr.append(crf)
		crf = crf+1

	dataFrameCr = pd.DataFrame({ 'geometry' : selcr , 'crlen': croprowLength , 'idg': geoidcr , 'crg': 'Generated by Crop Rows Generator v1' })
	geoDataFrameCropRows=gpd.GeoDataFrame(dataFrameCr, crs=crsEpsgId)
	cropRowsFileNameByGeom= os.path.join(dirPathLines,'croprows_lines.shp')
	geoDataFrameCropRows.to_file(driver = 'ESRI Shapefile', filename=str(cropRowsFileNameByGeom))

	##EXPORT CROP ROWS RESULTS TO WGS84 SHP AND KML FORMATS
	crsExportID = {'init': 'epsg:'+str(crglobals.EXPORT_EPSG)}
	exportCropRowsShapeFile = os.path.join(os.path.dirname(os.path.dirname(dirPathLines)),crglobals.EXPORTDIR,'croprows_wgs84.shp')
	geoDataFrameCropRowsWGS84=gpd.GeoDataFrame(dataFrameCr, crs=crsEpsgId)
	geoDataFrameCropRowsWGS84 = geoDataFrameCropRowsWGS84.to_crs(crsExportID) 
	geoDataFrameCropRowsWGS84.to_file(driver = 'ESRI Shapefile', filename=str(exportCropRowsShapeFile))
	exportCropRowsShapeFileKML= os.path.join(os.path.dirname(os.path.dirname(dirPathLines)),crglobals.EXPORTDIR,'croprows_wgs84.kml')
	geoDataFrameCropRowsWGS84.to_file(driver = 'kml', filename=str(exportCropRowsShapeFileKML))
	crutils.printLogMsg( crglobals.DONE_MSG+'Exported Resulting Crop Rows to KML and SHP format in WGS84 CRS' )

	cropRowsBufferFileName= os.path.join(dirPathLines,'croprows_lines_buffer.shp')
	cropRowsLinesBuffer = geoDataFrameCropRows.buffer(0.3)
	cropRowsLinesBufferGeoData=gpd.GeoDataFrame(crs=crsEpsgId,geometry=cropRowsLinesBuffer)
	cropRowsLinesBufferGeoData.to_file(driver = 'ESRI Shapefile', filename=str(cropRowsBufferFileName))


	#####################################
	## OLD CROPROWS - STAT SEARCH
	#####################################
	getIndexes = lambda x, xs: [i for (y, i) in zip(xs, range(len(xs))) if x == y]
	cuttedLineArray = []
	#look for 
	k=[]
	flagCounter3=0
	for x in distancesFiltered:
		#print(distancesFiltered[i])
		#print(getIndexes(distancesFiltered[i],newobjdistances))
		k.append(getIndexes(distancesFiltered[flagCounter3],geoDistance)[0])
		flagCounter3=flagCounter3+1

	#Reindex lines filtered
	index2 = []
	flagCounter2 = 0
	m=[]
	j=0
	croprowLength = []
	for x in k:
		m.append(dataFrameCandidateLines[k[j]])
		index2.append(flagCounter2)
		#line len for each geometry
		croprowLength.append( m[j].length )
		flagCounter2 +=1
		j=j+1
	
	#print('index2:')	
	#print(index2)
	#print('k')
	#print(k)
	#print('m')
	#print(m)

	
	sortdistance2 = np.argsort(distancesFiltered).astype('int')
	idByGeo2 = [x for _,x in sorted(zip(sortdistance2,index2))]

	#print('idByGeo2')
	#print(idByGeo2)

	crutils.printLogMsg(crglobals.DONE_MSG+'Re-indexing candidate lines !')

	#Fix distances substracting projectDistance
	arrayDistances = np.array(distancesFiltered)
	#fixdist = arrayDistances - projectDistance
	crutils.printLogMsg(crglobals.DONE_MSG+'Distances fixed !')

	#print(croprowLength)

	#fixdist
	dataFrameFixedLines = pd.DataFrame({ 'id': k  , 'geo_dist': arrayDistances , 'idgeo': idByGeo2 , 'crlen': croprowLength })
	#dataFrameFixedLines = pd.DataFrame({  })
	geoDataFrameFixedLines=gpd.GeoDataFrame(dataFrameFixedLines,crs=crsEpsgId, geometry=m)		
	geoDataFrameFixedLines.dropna()

	crutils.printLogMsg(crglobals.DONE_MSG+'Result lines generated !')

	cropRowsLinesFileName= os.path.join(dirPathLines,'croprows_lines_stat.shp')
	geoDataFrameFixedLines.to_file(driver = 'ESRI Shapefile', filename=str(cropRowsLinesFileName))

	

	crutils.printLogMsg(crglobals.DONE_MSG+'Writing file with resulting lines : %s ' % (cropRowsLinesFileName))

	#saveResultXMLFile(cropRowsLinesFileName)
	resultingFiles =[ cropRowsFileNameByGeom, 
					cropRowsBufferFileName, 
					exportCropRowsShapeFile, 
					exportCropRowsShapeFileKML,
					str(epsgValue),
					str(len(newObjDistancesSorted)),
					str(len(distancesFiltered)),
					vectorMask]
	saveResultXMLFile(resultingFiles)
	#saveResultXMLFile(cropRowsFileNameByGeom,cropRowsBufferFileName,exportCropRowsShapeFile,exportCropRowsShapeFileKML)

	#####################################

	return 1

def min_distance(point, lines):
    return lines.distance(point).min()

def postProcessingLines(cfgPostProcessingLines):
	
	"""
	postProcessingLines.
	
	:param cfgPostProcessingLines: (Array) lines postprocessing config array.
	:returns: none.
    """

	##Extend All Lines
	##print('=========================================')
	##print('Extend all Lines and Clip by Mask')
	tilesDirName = cfgPostProcessingLines[0]
	epsgValue = cfgPostProcessingLines[1]
	nCols = cfgPostProcessingLines[2]
	nRows = cfgPostProcessingLines[3]
	imagePathVectorMask = cfgPostProcessingLines[4]
	seedValue = cfgPostProcessingLines[5]

	#tilesDirName+'/'+crglobals.VECTORDIR+'/'+crglobals.OBJDIR
	obDir = os.path.join(tilesDirName, crglobals.VECTORDIR, crglobals.OBJDIR)

	startTime = time.time()
	############################################################################################
	#Multiprocessing Task
	processingCores = (multiprocessing.cpu_count())
	crutils.printLogMsg(crglobals.CHECK_MSG+"Number of CPU cores: %s" % (str(processingCores)) )
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	processingPool = multiprocessing.Pool(processes=(processingCores+2))
	results = [processingPool.apply(extendAllLinesInParallel, args=(tilesDirName,epsgValue,i,j,imagePathVectorMask,seedValue,)) for i in range(nCols) for j in range(nRows)]
	#print(results)
	processingPool.close()
	#while len(active_children()) > 1:
	#	print('Still active children process for -> extendAllLinesInParallel')
	#	time.sleep(0.5)
	processingPool.join()
	############################################################################################
	endTime = time.time()
	elapsedTime = endTime - startTime
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	# print total image generation time
	crutils.printLogMsg(crglobals.DONE_MSG+"extendAllLinesInParallel generation")
	crutils.printLogMsg(crglobals.DONEEND_MSG+"Total processing time: "+str(round(elapsedTime,2)) + " seconds")
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)

	#Old way: no parallelized task
	#extendAllLines(tilesDirName,epsgValue,nCols,nRows,imagePathVectorMask,seedValue)
	
	##Merge All Lines
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	crutils.printLogMsg(crglobals.START_MSG+'Merge All Lines')
	mergeAllLines(obDir,epsgValue)
	
    ##Extend All Lines
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	crutils.printLogMsg(crglobals.START_MSG+'Extend All Lines')
	extendAllMergedLines(obDir,imagePathVectorMask,epsgValue)

	##Merge All Points
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	crutils.printLogMsg(crglobals.START_MSG+'Merge All Points')
	mergeAllPoints(obDir,epsgValue)

	return 1

def main():
	"croprows geo module"
	print('croprows_geo [ module loaded ]')

main()
