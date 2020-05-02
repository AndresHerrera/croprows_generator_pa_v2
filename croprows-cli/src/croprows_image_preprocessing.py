# -*- coding: UTF-8 -*-
"""Crop Rows Image Processing

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""

from __future__ import division
from PIL import Image
import warnings
import random
import os
import time
import numpy as np
import cv2
import math
from math import sin,cos,radians

import imutils_perspective as imutils

import croprows_globals as crglobals
import croprows_utils as crutils


def readRGBImageByUrl(inputRasterImage):

	"""
    readRGBImageByUrl.
       
    :param inputRasterImage: (String) input image filename
    :returns outputRasterImage: (Image) RGB Image
    """

	bgr = cv2.imread(inputRasterImage)
	outputRasterImage = bgr[...,::-1]
	return outputRasterImage

def histogramEqualize(inputRasterImage):

	"""
    histogramEqualize.
       
    :param inputRasterImage: (Image) input image 
    :returns outputRasterImage: (Image) Equalized Image
    """
	imageYUV = cv2.cvtColor(inputRasterImage, cv2.COLOR_RGB2YUV)
	## equalize the histogram of the Y channel
	imageYUV[:,:,0] = cv2.equalizeHist(imageYUV[:,:,0])
	## convert the YUV image back to RGB format
	outputRasterImage = cv2.cvtColor(imageYUV, cv2.COLOR_YUV2RGB)
	return outputRasterImage

def smoothingPreProcessing(inputRasterImage, mW, gW):
	"""
	smoothingPreProcessing.
	
	:param inputRasterImage: (Image) input image.
	:param mW: (double) param mW.
	:param gW: (double) param gW.
	:returns medianBlurImage: (Image) median blur Image.
	:returns gausianBlurImage: (Image) gausian blur Image.
	"""
	medianWindow = mW
	gaussianWindow = gW

	medianBlurImage = cv2.medianBlur(inputRasterImage, medianWindow)
	gausianBlurImage = cv2.GaussianBlur(medianBlurImage,(gaussianWindow,gaussianWindow),0)
	return medianBlurImage, gausianBlurImage


def adjustGamma(inputRasterImage, gamma=1.0):
	"""
	ajustGamma.

	:param inputRasterImage: (Image) input raster image.
	:param gamma: (double) gamma value.
	:returns outputRasterImage: (Image) output raster image.
	"""
    #taken from https://www.pyimagesearch.com/2015/10/05/opencv-gamma-correction/
    #build a lookup table mapping the pixel values [0, 255] to
    #their adjusted gamma values
    
	invGamma = 1.0 / gamma
	lookUpTable = np.array([((i / 255.0) ** invGamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")
			# apply gamma correction using the lookup table
	outputRasterImage = cv2.LUT(inputRasterImage, lookUpTable)
	return 	outputRasterImage




def exgThresholdOtsu(inputRasterImage):
	
	"""
	exgThresholdOtsu.
	
	:param inputRasterImage: (Image) input raster image.
	:returns outputRasterImage: (Image) output raster image.
	"""

	imageArray = np.uint8(inputRasterImage*255)
	blurImage = cv2.GaussianBlur(imageArray,(5, 5), 2)
	#threshold = cv2.adaptiveThreshold(imageArray,255,cv2.ADAPTIVE_THRESH_MEAN_C , cv2.THRESH_BINARY_INV,11,2) poor results
	ret, threshold =cv2.threshold(blurImage, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	outputRasterImage = threshold
	return outputRasterImage 


## ExG
def calcExGIndex(inputRasterImage,mode):

	"""
	calcExGIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:param mode: (String) mode RGB or GBR
	:returns outputRasterImage: (Image) output raster image.
	"""

	if mode=='RGB' :
		chRed,chGreen,chBlue = cv2.split(inputRasterImage)
	else:
		chGreen,chRed,chBlue = cv2.split(inputRasterImage)
	
	normRed = chRed/255.0
	normGreen = chGreen/255.0
	normBlue = chBlue/255.0
	r= normRed/(normRed+normGreen+normBlue)
	g= normGreen/(normRed+normGreen+normBlue)
	b= normBlue/(normRed+normGreen+normBlue)
	outputRasterImage = (2*g - r - b)	
	return outputRasterImage

## ExR 
def calcExRIndex(inputRasterImage,mode):

	"""
	calcExRIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:param mode: (String) mode RGB or GBR
	:returns outputRasterImage: (Image) output raster image.
	"""

	if mode=='RGB' :
		chRed,chGreen,chBlue = cv2.split(inputRasterImage)
	else:
		chGreen,chRed,chBlue = cv2.split(inputRasterImage)

	normRed = chRed/255.0
	normGreen = chGreen/255.0
	normBlue = chBlue/255.0
	r= normRed/(normRed+normGreen+normBlue)
	g= normGreen/(normRed+normGreen+normBlue)
	b= normBlue/(normRed+normGreen+normBlue)
	outputRasterImage = (1.4*r - g)
	return outputRasterImage

## ExR 
def calcCIVEIndex(inputRasterImage,mode):

	"""
	calcCIVEIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:param mode: (String) mode RGB or GBR
	:returns outputRasterImage: (Image) output raster image.
	"""

	if mode=='RGB' :
		chRed,chGreen,chBlue = cv2.split(inputRasterImage)
	else:
		chGreen,chRed,chBlue = cv2.split(inputRasterImage)

	normRed = chRed/255.0
	normGreen = chGreen/255.0
	normBlue = chBlue/255.0
	r= normRed/(normRed+normGreen+normBlue)
	g= normGreen/(normRed+normGreen+normBlue)
	b= normBlue/(normRed+normGreen+normBlue)
	outputRasterImage = (0.441*r - 0.811*g + 0.385*b + 18.78745)
	return outputRasterImage


## ExG - ExR
def calcExGlessExGIndex(inputRasterImage,mode):

	"""
	calcExGlessExGIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:param mode: (String) mode RGB or GBR
	:returns outputRasterImage: (Image) output raster image.
	"""

	outputRasterImage = calcExGIndex(inputRasterImage,mode)-calcExRIndex(inputRasterImage,mode)
	return outputRasterImage


## NDI 
def calcNDIIndex(inputRasterImage,mode):

	"""
	calcNDIIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:param mode: (String) mode RGB or GBR
	:returns outputRasterImage: (Image) output raster image.
	"""

	if mode=='RGB' :
		chRed,chGreen,chBlue = cv2.split(inputRasterImage)
	else:
		chGreen,chRed,chBlue = cv2.split(inputRasterImage)

	normRed = chRed/255.0
	normGreen = chGreen/255.0
	normBlue = chBlue/255.0
	r= normRed/(normRed+normGreen+normBlue)
	g= normGreen/(normRed+normGreen+normBlue)
	b= normBlue/(normRed+normGreen+normBlue)
	outputRasterImage = (g-r)/(g+r)
	return outputRasterImage

## Calc NDVI
def contrastStretch(inputRasterImage):
	
	"""
	contrastStretch.
	
	:param inputRasterImage: (Image) input raster image.
	:returns outputRasterImage: (Image) output raster image.
	"""
    ##Performs a simple contrast stretch of the given image, from 5-95%.
	in_min = np.percentile(inputRasterImage, 5)
	in_max = np.percentile(inputRasterImage, 95)
	out_min = 0.0
	out_max = 255.0
	outputRasterImage = inputRasterImage - in_min
	outputRasterImage *= ((out_min - out_max) / (in_min - in_max))
	outputRasterImage += in_min
	return outputRasterImage

def calcNDVIIndex(inputRasterImage,mode):

	"""
	calcNDVIIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:param mode: (String) mode RGB or GBR
	:returns outputRasterImage: (Image) output raster image.
	"""

	if mode=='RGB' :
		chRed,chGreen,chBlue = cv2.split(inputRasterImage)
	else:
		chGreen,chRed,chBlue = cv2.split(inputRasterImage)
		#r, g, b = cv2.split(inputRasterImage)
		# Calculate the NDVI
		# Bottom of fraction
	bottom = (chRed.astype(float) + chBlue.astype(float))
	bottom[bottom == 0] = 0.01  # Make sure we don't divide by zero!
	outputNdviImage = (chRed.astype(float) - chBlue) / bottom
	outputNdviImage = contrastStretch(outputNdviImage)
	outputNdviImage = outputNdviImage.astype(np.uint8)
	return outputNdviImage



## Preprocessing Task (1)
def imagePreProcessing(inputRasterImage):

	"""
	imagePreProcessing.
	
	:param inputRasterImage: (Image) input raster image.
	:returns outputRasterImage: (Image) output raster image.
	"""

	gammaAdjusted = adjustGamma(inputRasterImage,1)
	medianBlurImage, gausianBlurImage = smoothingPreProcessing(gammaAdjusted, 3,5)
	outputRasterImage = gausianBlurImage
	return outputRasterImage

## Vegetation Index Generation Task (2)
def imageVegetationIndex(inputRasterImage):

	"""
	imageVegetationIndex.
	
	:param inputRasterImage: (Image) input raster image.
	:returns outputRasterImage: (Image) output raster image.
	"""


	#hsv = cv2.cvtColor(inputRasterImage, cv2.COLOR_RGB2HSV)
	#H, S, V = cv2.split(hsv)

	#outputRasterImage = calcExGlessExGIndex(inputRasterImage,'RGB')
	#outputRasterImage = calcExRIndex(inputRasterImage,'RGB')
	outputRasterImage = calcExGIndex(inputRasterImage,'RGB')
	#outputRasterImage = calcCIVEIndex(inputRasterImage,'RGB')
	#outputRasterImage = calcNDIIndex(inputRasterImage,'RGB')
	return outputRasterImage

## Segmentation Task (3)
def imageSegmentation(inputRasterImage):

	"""
    imageSegmentation.
       
    :param inputRasterImage: (Image) image to process.
	:returns outputRasterImage: (Image) output image.
    """

	thresOtsu = exgThresholdOtsu(inputRasterImage)
	#Try to Fill and Remove Small objects
	kernel = np.ones((9,9),np.uint8)
	opening = cv2.morphologyEx(thresOtsu, cv2.MORPH_OPEN, kernel)
	kernel = np.ones((3,3),np.uint8) #5
	dilation = cv2.dilate(opening,kernel,iterations = 9)
	#kernel = np.ones((9,9),np.uint8)
	#erosion = cv2.erode(dilation,kernel,iterations = 3)
	kernel = np.ones((20,20),np.uint8) #20
	erosion = cv2.erode(dilation,kernel,iterations = 9)
	#https://stackoverflow.com/questions/42798659/how-to-remove-small-connected-objects-using-opencv
	nb_components, output_, stats, centroids = cv2.connectedComponentsWithStats(erosion, connectivity=8)
	sizes = stats[1:, -1]; nb_components = nb_components - 1
	img2 = np.zeros((output_.shape))
	#for every component in the image, you keep it only if it's above min_size
	for i in range(0, nb_components):
		if sizes[i] >= crglobals.IMAGESEGMENTATION_MINSIZE:
			img2[output_ == i + 1] = 255  #255
	imageMask=img2.astype(np.uint8)	
	#cv2.floodFill(im_floodfill, mask, (0,0), 255);
	kernel = np.ones((9,9), np.uint8)
	image_blurred = cv2.erode(imageMask, kernel, iterations=3)
	median = cv2.medianBlur(image_blurred,15)
	outputRasterImage = median
	
	#median#image_blurred#imageMask#erosion


	# noise removal
	#kernel = np.ones((3,3),np.uint8)
	#opening = cv2.morphologyEx(outputRasterImage,cv2.MORPH_OPEN,kernel, iterations = 2)
	# sure background area
	#sure_bg = cv2.dilate(opening,kernel,iterations=3)
	# Finding sure foreground area
	#dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
	#ret, sure_fg = cv2.threshold(dist_transform,0.7*dist_transform.max(),255,0)
	# Finding unknown region
	#sure_fg = np.uint8(sure_fg)
	#outputRasterImage = cv2.subtract(sure_bg,sure_fg)

	return outputRasterImage	

## Green Mask 
def imageGreenMask(inputRasterImage):

	"""
    imageGreenMask.
       
    :param inputRasterImage: (Image) image to process.
	:returns greenMaskImage: (Image) green mask image.
    :returns bitwiseOutputImage: (Image) bitwise output image.
    """

	gaussianBlur = cv2.GaussianBlur(inputRasterImage, (7,7),0)
	hsv = cv2.cvtColor(gaussianBlur, cv2.COLOR_RGB2HSV)
	# lower bound
	lowerBoundGreen = np.array([60 - crglobals.GREENDETECTION_SENSITIVITY, 30, 30] )  #[40,70,70])
	# upper bound
	upperBoundGreen = np.array([80 + crglobals.GREENDETECTION_SENSITIVITY, 255, 255])#[80,200,200]
	maskGreen = cv2.inRange(hsv, lowerBoundGreen, upperBoundGreen)
	kernelOpen=np.ones((9,9))
	kernelClose=np.ones((9,9))
	maskOpen=cv2.morphologyEx(maskGreen,cv2.MORPH_OPEN,kernelOpen)
	maskClose=cv2.morphologyEx(maskOpen,cv2.MORPH_CLOSE,kernelClose)
	# #https://stackoverflow.com/questions/42798659/how-to-remove-small-connected-objects-using-opencv
	nb_components, output_, stats, centroids = cv2.connectedComponentsWithStats(maskClose, connectivity=8)
	sizes = stats[1:, -1]; nb_components = nb_components - 1
	greenMaskImage = np.zeros((output_.shape))
	#kernel = np.ones((3,3), np.uint8)
	#greenMaskImage = cv2.erode(greenMaskImage, kernel, iterations=3)
	# #for every component in the image, you keep it only if it's above min_size
	for i in range(0, nb_components):
	 	if sizes[i] >= crglobals.GREENDETECTION_MINSIZE:
	 		greenMaskImage[output_ == i + 1] = 255.0
	imageMask=greenMaskImage.astype(np.uint8)
	#bitwiseOutputImage = cv2.bitwise_and(inputRasterImage, inputRasterImage, mask = imageMask)

	#some changes 3-9-2018
	distanceMask = cv2.distanceTransform(imageMask, cv2.DIST_L2, 0)
	cv2.normalize(distanceMask, distanceMask, 0, 1.0, cv2.NORM_MINMAX)
	_, distanceMask = cv2.threshold(distanceMask, 0.4, 1, cv2.THRESH_BINARY) #0.4
	# Dilate a bit the dist image
	kernel1 = np.ones((3,3), dtype=np.uint8)
	distanceMask = cv2.dilate(distanceMask, kernel1)
	#fixing using distanceMask as a green color detection mask
	greenMaskImage = distanceMask
	imageMaskDist=greenMaskImage.astype(np.uint8)
	bitwiseOutputImage = cv2.bitwise_and(inputRasterImage, inputRasterImage, mask = imageMaskDist)

 
	return greenMaskImage, bitwiseOutputImage , distanceMask




def autoCannyEdgeDetection(inputRasterImage, sigma=0.33):
	
	"""
    autoCannyEdgeDetection.
       
    :param inputRasterImage: (Image) image to process
	:param sigma: (double) sigma value
    :returns outputRasterImage: (Image) outputRasterImage.
    """
	#kernel=(3,3)
	#kernel = np.ones(kernel, np.uint8)
	#thresh = cv2.morphologyEx(inputRasterImage, cv2.MORPH_OPEN, kernel)
	#thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,kernel, iterations=4)
	#inputRasterImage = cv2.GaussianBlur(thresh, (3,3), 0)
	# compute the median of the single channel pixel intensities
	v = np.median(inputRasterImage)
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edgedCanny = cv2.Canny(inputRasterImage, lower, upper)
	#kernel = np.ones((20,20), np.uint8)
    #image_eroded = cv2.erode(edged, kernel, iterations=3)
	outputRasterImage = edgedCanny
	return outputRasterImage


def buildContours(inputRasterImage,seed, tolerance):

	"""
	buildContours.

	:param inputRasterImage: (Image) image.
	:param seed: (int) seed.
	:param tolerance: (double) tolerance.
	:returns imgContours: (Array) imgContours.
	:returns contoursAll: (Array) contoursAll.
	:returns contoursFiltred: (Array) contoursFiltred.
	:returns angleFitMinAreaRect: (double) angleFitMinAreaRect.
	:returns meanAngleFitMinAreaRect: (double) meanAngleFitMinAreaRect.
	:returns angleFitElipseContours: (double) angleFitElipseContours.
	:returns meanAngleFitElipseContours: (double) meanAngleFitElipseContours.
    """

	##################################################
	##   Seed Cases
	##
	##   __  case 1
	##
	##   |   case 2
	##   
	##   /   case 3
	##
	##   \   case 4
	##
	##   O   case -1 auto search 
	##
	##################################################
	## Tolerance +/- in degrees
	##################################################

	#contoursFiltred = []
	angleFitMinAreaRect = []
	angleFitElipseContours = []
	#meanAngleFitMinAreaRect = []
	#meanAngleFitElipseContours = []
	#angleFitElipseContours = []
	#imgEdges = autoCannyEdgeDetection(inputRasterImage) #Calculate edge using Canny operator
	#autocanny_canny = imgEdges.copy()
	imgEdges = inputRasterImage
	imgContours, contoursAll, hierarchy = cv2.findContours(inputRasterImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	
	######
	## preProcessingContours
	######
	contoursAll = crutils.preProcessingContours(contoursAll)
	######
	## preProcessingFilteredContours
	######
	contoursFiltred = crutils.preProcessingFilteredContours(contoursAll)

	flagCounterContour=0

	crutils.printLogMsg(crglobals.SEPARATOR_MSG)
	crutils.printLogMsg(crglobals.OK_MSG+'Contour Count : %s' % (len(contoursFiltred)))

	for cc in contoursFiltred:
		minAreaRecContours = cv2.minAreaRect(cc)
		boxPointsContours = cv2.boxPoints(minAreaRecContours)
		angleContours = cv2.minAreaRect(boxPointsContours)[-1]
		angleFitMinAreaRect.append(angleContours)
		(x,y),(MA,ma),angleElipse = cv2.fitEllipse(cc)
		angleFitElipseContours.append(angleElipse)
		crutils.printLogMsg('Contour %s  - Max Angle: %s' % ((flagCounterContour+1), round(angleElipse,1)) )
		flagCounterContour +=1
			
	x=1
	seedCases = {
	  		-1: lambda x: crglobals.SEEDCASES[0],
	  		 1: lambda x: crglobals.SEEDCASES[1],
	  		 2: lambda x: crglobals.SEEDCASES[2],
	  		 3: lambda x: crglobals.SEEDCASES[3],
	  		 4: lambda x: crglobals.SEEDCASES[4]
		}[seed](x)

	low = seedCases[0] - tolerance
	high = seedCases[1]+tolerance
	angleFitElipseContours = list(filter(lambda x: x>=low, angleFitElipseContours))
	angleFitElipseContours = list(filter(lambda x: x<=high, angleFitElipseContours))

	sdAngle = (np.nanstd(angleFitElipseContours))
	crutils.printLogMsg('Contours Angle SD: %s' % round(sdAngle,1))
	maxAngle = (np.nanmax(angleFitElipseContours))
	crutils.printLogMsg('Contours Angle MAX: %s' % round(maxAngle,1))
	minAngle = (np.nanmin(angleFitElipseContours))
	crutils.printLogMsg('Contours Angle MIN: %s' % round(minAngle,1))
	avgAngle = (np.nanmean(angleFitElipseContours))
	crutils.printLogMsg('Contours Angle AVG: %s' % round(avgAngle,1))
	
	crutils.printLogMsg(crglobals.SEPARATOR_MSG)

	if( (len(angleFitElipseContours)> int(crglobals.CONTOURAVGMAX/2)+2)  and (sdAngle <= crglobals.MAXANGLEDESV) ):
		#replaced mean to nanmean
		try:
			meanAngleFitMinAreaRect = (np.nanmean(angleFitMinAreaRect))
			meanAngleFitElipseContours = (np.nanmean(angleFitElipseContours))
		except RuntimeWarning:
			meanAngleFitMinAreaRect = np.NaN
			meanAngleFitElipseContours = np.NaN
	else:
		meanAngleFitMinAreaRect = np.NaN
		meanAngleFitElipseContours = np.NaN
	
	outputRasterImage = imgEdges
	
	return outputRasterImage , imgContours , contoursAll , contoursFiltred, angleFitMinAreaRect , meanAngleFitMinAreaRect , angleFitElipseContours , meanAngleFitElipseContours


## Compose Tasks
def preProcessingPipeline(inputRasterImage):

	"""
    preProcessingPipeline.
       
    :param inputRasterImage: (Image) image to process
    :returns outputRasterImage: (Image) outputRasterImage.
	:returns maskRasterOut: (Image) mask_out.
	:returns vegetationIndexImage: (Image) vegetation index image.
    """

	preprocessedRasterImage = imagePreProcessing(inputRasterImage)
	vegetationIndexImage = imageVegetationIndex(preprocessedRasterImage)
	segmentedImage = imageSegmentation(vegetationIndexImage)
	#Adding Green Mask  (check is to slow)
	mask_,_,_bgmask = imageGreenMask(inputRasterImage)
	#same data type
	addSegmentedAndGreenMask = cv2.add(segmentedImage.astype(np.uint8),mask_.astype(np.uint8))
	#blur = cv2.GaussianBlur(addSegmentedAndGreenMask, (3,3),0)
	#median = cv2.medianBlur(blur,9)
	#kernel = np.ones((3,3), np.uint8)
	#image_eroded = cv2.erode(median, kernel, iterations=3)
	outputRasterImage = addSegmentedAndGreenMask
	sourceMaskRasterBGR=cv2.cvtColor(outputRasterImage,cv2.COLOR_GRAY2BGR)#change mask to a 3 channel image 
	maskRasterOut=cv2.subtract(sourceMaskRasterBGR,inputRasterImage)
	maskRasterOut=cv2.subtract(sourceMaskRasterBGR,maskRasterOut)

	return outputRasterImage ,  maskRasterOut , vegetationIndexImage, inputRasterImage


def drawContours(inputRasterImage, contours):
	"""
	drawContours.
	
	:param inputRasterImage: (Image) image to process.
	:param contours: (Contour) contours.
	:returns outputRasterImage: (Image) RasterImage.
	:returns outputImageContousSmallBoxes: (Image) ImageContousSmallBoxes.
	:returns cloneRasterImageForAxisInBox: (Image) RasterImageForAxisInBox.
	"""

	cloneRasterImageForContours = inputRasterImage.copy()
	cloneRasterImageForSmallBoxes = inputRasterImage.copy()
	cloneRasterImageForAxisInBox = inputRasterImage.copy()
	outputRasterImage = np.zeros((inputRasterImage.shape))
	outputImageContousSmallBoxes = np.zeros((inputRasterImage.shape))
	cmPerPixel = 1
	
	flagCounterContour = 0
	for c in contours:
	# find minimum area
		rect = cv2.minAreaRect(c)
		# calculate coordinates of the minimum area rectangle
		box = cv2.boxPoints(rect)
		x_,y_,w_,h_ = cv2.boundingRect(box)
		angle_ = cv2.minAreaRect(box)[-1]
		box = imutils.order_points(box)
		# normalize coordinates to integers
		box = np.int0(box)
		M = cv2.moments(c)
		#cX = int(M["m10"] / M["m00"])
		#cY = int(M["m01"] / M["m00"])
		flagCounterContour +=1
		##Draw Contour
		drawContour = cv2.drawContours(cloneRasterImageForContours, contours, -1, (255, 0, 0), 2)
		#Draw id contour label
		#cv2.putText(cloneRasterImageForContours, "{}".format(round(angle_,1)), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
		##Draw Box 
		boxSmall = [box]
		#print(boxSmall)
		W = rect[1][0]
		H = rect[1][1]
		#if((H>crglobals.CONTOUR_HEIGHT_FILTER) and (W>crglobals.CONTOUR_WIDTH_FILTER)):
		outputImageContousSmallBoxes = cv2.drawContours(cloneRasterImageForSmallBoxes, boxSmall , 0, (0,0, 255), 3)
		#cv2.putText(cloneRasterImageForSmallBoxes, str(float(round(W,1))) + ","+ str(float(round(H,1)))     , (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
		#######
		#if w_ > crglobals.CONTOUR_WIDTH_FILTER:
		#if((H>crglobals.CONTOUR_HEIGHT_FILTER) and (W>crglobals.CONTOUR_WIDTH_FILTER)):
		if((H>0) and (W>0)):
			(x,y),radius = cv2.minEnclosingCircle(c)
			center = (int(x),int(y))
			radius = int(radius)
			cv2.circle(cloneRasterImageForAxisInBox,center, 2, (0,0,255), -1)
			thetaAngle = (np.pi/180.0)
			x2 = x + 1000 * np.cos(thetaAngle)
			y2 = y + 1000 * np.sin(thetaAngle)
			#angle_rota = 90 #(-(angle_) + (prom))
			#M = cv2.getRotationMatrix2D(center,angle_rota,1)
        	#pts = np.int0(cv2.transform(np.array(boxoriginal), M))[0]
        	#cv2.drawContours(cloneRasterImageForContours, [pts] , 0, (125,255, 125), 3)
        	#mass center
			#cv2.line(cloneRasterImageForContours,center,(int(x2),int(y2)),(255,125,0),3)
			(tl, tr, br, bl) = box # (top left, top right, bottom right, bottom left)
			#print(tl)
			(tltrX, tltrY) = crutils.midPoint(tl, tr) #Mid point between TOPLEFT Y TOPRIGHT
			(blbrX, blbrY) = crutils.midPoint(bl, br) #Mid point between BOTTOMLEFT Y BOTTOMRIGHT
			(tlblX, tlblY) = crutils.midPoint(tl, bl) #Mid point between TOPLEFT Y BOTTOMLEFT
			(trbrX, trbrY) = crutils.midPoint(tr, br) #Mid point between TOPRIGHT Y BOTTOMRIGHT
			cv2.circle(cloneRasterImageForAxisInBox,(int(tltrX), int(tltrY)), 2, (51,255,255), -1)
			cv2.circle(cloneRasterImageForAxisInBox,(int(blbrX), int(blbrY)), 2, (51,255,255), -1)
			cv2.circle(cloneRasterImageForAxisInBox,(int(tlblX), int(tlblY)), 2, (51,255,255), -1)
			cv2.circle(cloneRasterImageForAxisInBox,(int(trbrX), int(trbrY)), 2, (51,255,255), -1)
			distanceTLTRtoBLBR = math.sqrt(((tltrX-blbrX)**2)+((tltrY-blbrY)**2))
			distanceTLBLtoTRBR = math.sqrt(((tlblX-trbrX)**2)+((tlblY-trbrY)**2))
			if(distanceTLTRtoBLBR >= distanceTLBLtoTRBR ):
				cv2.line(cloneRasterImageForAxisInBox, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),(0, 255, 0), 2)
				linearDistanceInMeters = distanceTLTRtoBLBR * cmPerPixel
			else:
				#largest line
				cv2.line(cloneRasterImageForAxisInBox, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),(255, 0, 0), 2)
				linearDistanceInMeters = distanceTLBLtoTRBR * cmPerPixel
       
		outputRasterImage = drawContour
	return outputRasterImage , outputImageContousSmallBoxes , cloneRasterImageForAxisInBox


def main():
	"croprows image processing module"
	crutils.printLogMsg('croprows_image_processing [ module loaded ]')

main()