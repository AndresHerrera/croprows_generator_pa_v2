# croprows-cli

**croprows-cli** is the processing core that handles the most complex tasks and is accessed by a command line interface for **Crop Rows Generator 1.0  (CRG).**

## Requirements for stand alone execution 

- Python: *Python 2.7.12*

## Installation

1. Python installation
- sudo apt-get install python-setuptools python-pip python-dev build-essential
- sudo pip install --upgrade pip

2. Python Libreries
- sudo pip install opencv-python==3.1.0.5
- sudo pip install numpy==1.16.6
- sudo pip install scipy==1.2.3
- sudo pip install Fiona==1.8.13.post1
- sudo pip install Pillow==3.2.0
- sudo pip install joblib==0.14.1
- sudo pip install pandas==0.24.2
- sudo pip install geopandas==0.6.3
- sudo pip install geojson==2.5.0
- sudo pip install scikit-image==0.14.5
- sudo pip install scikit-learn==0.20.4
- sudo pip install flask==1.1.2
- sudo pip install flask_restful==0.3.8
- sudo pip install flask-cors==3.0.8
- sudo pip install request==2019.4.13
- sudo pip install requests==2.23.0


## Usage

- -h show help.
- -p processing crop rows in parallel mode.
- -s processing crop rows in serial mode.
- -debug disable debug messages
- -t change processing raster tile size.

## Examples
1. **Show help**
- $ ./run_croprows-cli.sh -h

2. **Perform a crop rows processing task**
- $ ./run_croprows-cli.sh croprowsproject.xml

3. **Perform a crop rows processing task in serial mode**
- $ ./run_croprows-cli.sh croprowsproject.xml -s

4. **Perform a crop rows processing task in parallel mode**
- $ ./run_croprows-cli.sh croprowsproject.xml -s

5. **Perform a crop rows processing task with out debug messages**
- $ ./run_croprows-cli.sh croprowsproject.xml -debug

6. **Perform a crop rows processing task with tile size 10 meters**
- $ ./run_croprows-cli.sh croprowsproject.xml -t 10

## License

croprows-cli is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

 
* <em>Copyright (c) 2019-2020 Andres Herrera, Universidad del Valle</em>
