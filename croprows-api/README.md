# croprows-api

**croprows-api** is a REST API exposes Crop Rows Generator (CRG) resources through on HTTP methods.

## Requirements for stand alone execution 

- Python: *Python 2.7.12*

## Installation

1. Python installation
- sudo apt-get install python-setuptools python-pip python-dev build-essential
- sudo pip install --upgrade pip

2. Python libraries
- sudo pip install flask==1.1.2
- sudo pip install flask_restful==0.3.8
- sudo pip install flask-cors==3.0.8
- sudo pip install request==2019.4.13
- sudo pip install requests==2.23.0

## Start API

./run_croprows-api.sh

## API

### Crop Rows API Status (JSON Response)
- http://server:2767/imlive - GET

### OS information (JSON Response)
- http://server:2767/os - GET

### Execute Crop Rows processing task for croprows-project-file.xml
- http://server:2767/croprows/croprows-project-file.xml - GET

### Upload orthomosaic-file to the server
- http://server:2767/crimageuploader/ - POST

`
curl -i -X POST "Content-Type: multipart/form-data" \
-F "image=@uploadfile.tif" http://localhost:2767/crimageuploader
`

### Upload vector mask-file to the server
- http://server:2767/crmaskuploader/ - POST

`
curl -i -X POST "Content-Type: multipart/form-data" \
-F "shp=@filemask.shp" \
-F "shx=@filemask.shx" \
-F "dbf=@filemask.dbf" http://localhost:2767/crmaskuploader
`

## License

croprows-api is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

 
* <em>Copyright (c) 2019-2020 Andres Herrera, Universidad del Valle</em>

