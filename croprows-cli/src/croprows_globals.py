# -*- coding: UTF-8 -*-
"""Crop Rows Globals 

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""

import os

CRVERSION = "1.0"

DEBUGMODE = True
SAVELOG = False
LOGFILE = "croprows.log"
EXPORT_EPSG = "4326"

##File Globals

#Results Directory FOR CROPROWS Files
CROPDIR 			= "results/"

RASTERDIR 			= "rasters"
VECTORDIR 			= "vectors"
EXPORTDIR			= "export"
OBJDIR 				= "obj"
COLPREFIX			= 'cl_'
ROWPREFIX 			= 'rw_'


PICNAME 			= 'mosaic'
JPG_EXT 			= '.jpg'
JPGX_EXT 			= '.jpgw'
GEOJSON_EXT 		= '.geojson'
AUX_EXT 			= '.aux.xml'

NPYOBJ 				= '.npy'

TILESENDNAME 		= 'tiles'
SEGMENTEDNAME 		= 'segmented'
MASKEDNAME			= 'masked'
EDGESNAME			= 'edges'
CONTOURSNAME		= 'contours'
COMPOSECONTNAME		= 'cimgcont'
COMPOSEBOXNAME		= 'cimgsboxes'
COMPOSEGEONAME		= 'cimggeoms'

VECTORLINES			= 'lines'
VECTORPOINTS 		= 'points'

DONE_MSG 			= '\x1b[6;30;42m[DONE]\x1b[0m '
DONEEND_MSG 		= '\x1b[0;32;44m[####]\x1b[0m '
FAIL_MSG 			= '\x1b[0;30;41m[FAIL]\x1b[0m '
OK_MSG 				= '\x1b[6;30;46m[*]\x1b[0m '
NO_MSG 				= '\x1b[6;30;41m[-]\x1b[0m '
ERROR_MSG 			= '\x1b[0;30;41m[ERROR]\x1b[0m '
CHECK_MSG 			= '\x1b[6;30;43m[CHECK]\x1b[0m '
START_MSG			= '\x1b[0;31;40m[->]\x1b[0m '
STOP_MSG			= '\x1b[0;31;40m[<-]\x1b[0m '
WORKER_MSG			= '\x1b[0;31;40m[WORKER]\x1b[0m '
SEPARATOR_MSG 		= '.........................................................'

#Crop rows generator global vars

SEEDCASES = [[-360,360],[-90,90],[-45,45],[0,90],[90,180]]
SEED_SPAN = 3

MAX_IMAGE_PIXELS_CFG = 1000000000 

DEF_TILESIZE_M = 20

CONTOUR_WIDTH_FILTER = 20 #20 #30 pref:20
CONTOUR_HEIGHT_FILTER = 20
CONTOUR_HEIGHT_FILTER_MAX = 80
#Use CONTOURAVGMAX filter
CONTOURAVGMAX = 10#10

#Max Angle Desviation for average
MAXANGLEDESV = 3#3

MINLINEDISTANCE = 0.4 #0.4 #0.5 #0.8 pref: 0.4

#Support pinaple furrow  > 0.8
MINCROPROWDISTANCE = 1.3
MAXCROPROWDISTANCE = 2 #2.2

GREENDETECTION_SENSITIVITY = 15 #15
GREENDETECTION_MINSIZE = 280 #300 #500 pref: 200

IMAGESEGMENTATION_MINSIZE= 400 #450 pref: 400 -> 50

EXTRAPOL_RATIO = 500

##################################
#avaliable modes
#- parallel
#- serial 
###################################
PROCESSING_MODE = os.environ.get('CRG_MODE')

welcome_str = '####################################################################'
welcome_str += '\n\n'
welcome_str += ' #####  ######  ####### ######  ######  ####### #     #  #####     \n'
welcome_str += '#     # #     # #     # #     # #     # #     # #  #  # #     #    \n'
welcome_str += '#       #     # #     # #     # #     # #     # #  #  # #          \n'
welcome_str += '#       ######  #     # ######  ######  #     # #  #  #  #####     \n'
welcome_str += '#       #   #   #     # #       #   #   #     # #  #  #       #    \n'
welcome_str += '#     # #    #  #     # #       #    #  #     # #  #  # #     #    \n'
welcome_str += ' #####  #     # ####### #       #     # #######  ## ##   #####     \n'
welcome_str += '                                                  Version '+CRVERSION+'		\n'
welcome_str += '\n'
welcome_str += '####################################################################'


end_str = '####################################################################'
end_str += '\n\n'
end_str += '####### #     # ######  \n'
end_str += '#       ##    # #     # \n'
end_str += '#       # #   # #     # \n'
end_str += '#####   #  #  # #     # \n'
end_str += '#       #   # # #     # \n'
end_str += '#       #    ## #     # \n'
end_str += '####### #     # ###### \n'
end_str += '\n'
end_str += '####################################################################'

done_str = '####################################################################'
done_str += '\n\n'
done_str += '######  ####### #     # ####### \n'
done_str += '#     # #     # ##    # #       \n'
done_str += '#     # #     # # #   # #       \n'
done_str += '#     # #     # #  #  # #####   \n'
done_str += '#     # #     # #   # # #       \n'
done_str += '#     # #     # #    ## #       \n'
done_str += '######  ####### #     # ####### \n'
done_str += '\n'
done_str += '####################################################################'


help_str = '####################################################################'
help_str += '\n\n'
help_str += 'Usage: ./run_croprows-cli.sh croprowsproject.xml \n\n\n'
help_str += 'CLI Commands:       \n\n'
help_str += '-h show this help\n'
help_str += '-p processing in parallel mode (by default)\n'
help_str += '-s processing in serial mode\n'
help_str += '-debug disable messages.\n'
help_str += '-t change processing raster tile size. \n\t usage:  -t 10\n'
help_str += '\n'
help_str += '####################################################################'


BANNER_WELCOME = welcome_str
BANNER_END = end_str
BANNER_DONE = done_str
HELP_MSG = help_str


def main():
	"""
    main. croprows_globals
       
    """
	print(BANNER_WELCOME)
	print('croprows_globals [ module loaded ]')

main()
