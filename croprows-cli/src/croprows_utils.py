# -*- coding: UTF-8 -*-
"""Crop Rows Utils

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""

from __future__ import division
import croprows_globals as crglobals
import os
import time
import numpy as np
import cv2
from scipy.interpolate import splprep, splev
import warnings

warnings.simplefilter("ignore", RuntimeWarning)


def getOpenCVVersion():
    """
    getOpenCVVersion.
       
    :param none: no input params.
    :returns: OpenCV version.
    """

    return 'OpenCV version:'+cv2.__version__

#Calculates Angle between two vectors
def angleBetween(startPoint, endPoint):

    """
    angleBetween.
       
    :param startPoint: (Point) start point.
    :param endPoint: (Point) end point.
    :returns angle: (double) angle in radians.
    """

    angleStartPoint = np.arctan2(*startPoint[::-1])
    angleEndPoint = np.arctan2(*endPoint[::-1])
    return np.rad2deg((angleStartPoint - angleEndPoint) % (2 * np.pi))	

def getAzimuth(startPointX,startPointY,endPointX,endPointY):

    """
    getAzimuth.
       
    :param startPointX: (double) x coord of start point.
    :param startPointY: (double) y coord of start point.
    :param endPointX: (double) x coord of end point.
    :param endPointY: (double) y coord of end point.
    :returns azimuthAngle: (double) angle in radians.
    """

    azimuthAngle = np.arctan2(endPointX - startPointX, endPointY - startPointY)
    azimuthAngle=np.degrees(azimuthAngle)if azimuthAngle>0 else np.degrees(azimuthAngle) + 360
    return azimuthAngle

#Calc mid point betwwen two cordinates 
def midPoint(startPoint, endPoint):

    """
    midPoint.
       
    :param startPoint: (Point) start point.
    :param endPoint: (Point) end point.
    :param endPointX: (double) x coord of end point.
    :param endPointY: (double) y coord of end point.
    :returns midPoint: (Point) mid point.
    """
    midPointValue = (startPoint[0] + endPoint[0]) / 2, (startPoint[1] + endPoint[1]) / 2
    return midPointValue   

#returns file index
def fileNumberIndex(x):

    """
    fileNumberIndex.
       
    :param x: (String) file index.
    :returns x[0]: (String) split file index.
    """

    return(x.split('_')[0])	

#Range
def setRange(start, end, step):

    """
    setRange.
       
    :param start: (int) start value.
    :param end: (int) end value.
    :param step: (int) step value.
    :returns range: (list) list of number generated
    """

    while start <= end:
        yield start
        start += step 

#Find if contour is close
def findIfClose(firstContour,secondContour):

    """
    findIfClose. Find if contour is close
       
    :param firstContour: (Contour) start value.
    :param secondContour: (Contour) end value.
    :returns range: (boolean) 1: if contour is close 0: is not close 
    """

    row1,row2 = firstContour.shape[0],secondContour.shape[0]
    for i in range(row1):
        for j in range(row2):
            dist = np.linalg.norm(firstContour[i]-secondContour[j])
            if abs(dist) < 1 :
                return True
            elif i==row1-1 and j==row2-1:
                return False  


def preProcessingContours(contoursAll):

    """
    preProcessingContours. Pre processing contours
       
    :param contoursAll: (Contour) all contours
    :returns smoothedContoursArray: (Contour) all smoothed contours preprocessed 
    """

    #Merge Clossing Contours
    #Extreme slow pre-processing 
    #LENGTH = len(contoursAll)
    #status = np.zeros((LENGTH,1))
    #for i,cnt1 in enumerate(contoursAll):
    #   x = i
    #   if i != LENGTH-1:
    #       for j,cnt2 in enumerate(contoursAll[i+1:]):
    #           x = x+1
    #           dist = crutils.findIfClose(cnt1,cnt2)
    #           if dist == True:
    #               val = min(status[i],status[x])
    #               status[x] = status[i] = val
    #           else:
    #               if status[x]==status[i]:
    #                   status[x] = i+1
    #unified = []
    #maximum = int(status.max())+1
    #for i in range(maximum):
    #   pos = np.where(status==i)[0]
    #   if pos.size != 0:
    #       cont = np.vstack(contoursAll[i] for i in pos)
    #       hull = cv2.convexHull(cont)
    #       unified.append(hull)
    #contoursAll = unified

    #contoursFiltred2 = sorted(contoursAll, key = cv2.contourArea, reverse = True)[:5] 
    #contourSorted, boundingBoxes = sortContours(contoursAll, method="left-to-right")

    filteredContoursArray = []
    for c in contoursAll:
        rect = cv2.minAreaRect(c)
        M = cv2.moments(c)
        W = rect[1][0]
        H = rect[1][1]

        #adding ratio 3-09-2018
        ratio = H/W

        #and (H<crglobals.CONTOUR_HEIGHT_FILTER_MAX) and ( ratio < 2 )  
        
        if((H>crglobals.CONTOUR_HEIGHT_FILTER) 
        and (W>crglobals.CONTOUR_WIDTH_FILTER) ):
            #print("W: %s H: %s - ratio: %s" % ( str(round(W,2)) , str(round(H,2)) , str(round(ratio,2))   ))
            filteredContoursArray.append(c)

    #contoursAll = filteredContoursArray #contourSorted

    smoothedContoursArray = []
    for contour in filteredContoursArray:
        x,y = contour.T
        # Convert from numpy arrays to normal arrays
        x = x.tolist()[0]
        y = y.tolist()[0]
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.interpolate.splprep.html
        tck, u = splprep([x,y], u=None, s=1.0, per=1)
        # https://docs.scipy.org/doc/numpy-1.10.1/reference/generated/numpy.linspace.html
        u_new = np.linspace(u.min(), u.max(), 25)
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.interpolate.splev.html
        x_new, y_new = splev(u_new, tck, der=0)
        # Convert it back to numpy format for opencv to be able to display it
        res_array = [[[int(i[0]), int(i[1])]] for i in zip(x_new,y_new)]
        smoothedContoursArray.append(np.asarray(res_array, dtype=np.int32))
    
    contoursAll = smoothedContoursArray
    
    return contoursAll

def preProcessingFilteredContours(contoursAll):

    """
    preProcessingFilteredContours. Pre processing  filtered contours
       
    :param contoursAll: (Contour) all contours
    :returns contoursFiltered: (Contour) all contours filtered 
    """

    contoursFiltered = contoursAll
    #Filter Contours by Max Area
    contoursFiltered = sorted(contoursFiltered, key = cv2.contourArea, reverse = True)[:crglobals.CONTOURAVGMAX] 
    ## TODO: Filter contors by seed criteria

    return contoursFiltered

#Sort Contours

def sortContours(contours, method="left-to-right"):

    """
    sortContours. Sort Contours
        See: https://www.pyimagesearch.com/2015/04/20/sorting-contours-using-python-and-opencv/
       
    :param contours: (Contour) contours to be sorted
    :param method: (Options) left-to-right , bottom-to-top , top-to-bottom 
    :returns contours: (Contour)  list of sorted contours 
    :returns boundingBoxes: (BBox)  list of sorted bounding boxes
    """

    # initialize the reverse flag and sort index
    reverse = False
    i = 0
    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True
    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in contours]
    (contours, boundingBoxes) = zip(*sorted(zip(contours, boundingBoxes),
        key=lambda b:b[1][i], reverse=reverse))
    # return the list of sorted contours and bounding boxes
    return (contours, boundingBoxes)       


def removeAdjacentsInArray(contourArray):
    """
    removeAdjacentsInArray. remove adjacents in array
       
    :param contourArray: (Array) all contours
    :returns noAdjacentsArray: (Array) adjacents removed and with last array value
    """
    noAdjacentsArray = []

    if(len(contourArray)> 0):
        #r = [a for a,b in zip(contourArray, contourArray[1:]+[not contourArray[-1]]) if a != b]
        #fixed - included last array value
        noAdjacentsArray = [a for a,b in zip(contourArray, contourArray[1:]+[not contourArray[-1]]) if a != b]+[contourArray[-1]]
    else:
        noAdjacentsArray = []
    return noAdjacentsArray




#Print LOG 

def printLogMsg(msgString):

    """
    printLogMsg. print in console messages
       
    :param msgString: (String) message to be printed
    :returns stdout: (String) message
    """

    if(crglobals.DEBUGMODE):
        if(crglobals.SAVELOG):
            #TODO: implements log file saving
            print('Save in log file: %s' % (crglobals.LOGFILE) )
            print(msgString)
        else:
            print(msgString)


def makeDirectory(dirPath):

    """
    makeDirectory. print in console messages
       
    :param dirPath: (os.path) message to be printed
    :returns none: (void)
    """

    try:
        os.stat(dirPath)
        printLogMsg(crglobals.CHECK_MSG+'Skip directory creation %s' % (dirPath))
    except:
        os.mkdir(dirPath)
        printLogMsg(crglobals.DONE_MSG+'Directory creation was successful %s' % (dirPath))

def main():
    "croprows utils module"
    printLogMsg('croprows_utils [ module loaded ]')

main()
