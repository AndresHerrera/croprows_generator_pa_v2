"""Crop Rows Generator API
This plugin generates crop rows lines from drone aerial images

    :author: Andres Herrera
    :begin: 2018-02-22
    :copyright: 2018 by Andres Herrera - Universidad del Valle
    :email: fabio.herrera@correounivalle.edu.co

    This program is free software; you can redistribute it and/or modify   it under the terms of the GNU General Public License as published by  the Free Software Foundation; either version 2 of the License, or 
    (at your option) any later version.  This script initializes the plugin, making it known to QGIS.

"""

"""
.. module:: croprows-api.py
   :synopsis: API Server croprows

.. moduleauthor:: Andres Herrera <fabio.herrera@correounivalle.edu.co>

"""

from flask import Flask, jsonify, make_response,  request, Response
from flask_cors import CORS
import subprocess
import time
import os
import os.path
import sys
import json
import requests


UPLOAD_FOLDER = 'orthomosaics'
ALLOWED_EXTENSIONS = set(['tif', 'shp', 'shx', 'dbf'])

app = Flask(__name__,static_url_path='',static_folder='')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_platform():
    """
    get_platform. Get current S.O
       
    :returns None: None.
    """
    platforms = {
        'linux1' : 'Linux',
        'linux2' : 'Linux',
        'darwin' : 'OS X',
        'win32' : 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform
    return platforms[sys.platform]

@app.route('/')
@app.route('/index.htm')
@app.route('/index.html')
@app.route('/croprows')
def index():
    """
    index. Start API Server
       
    :returns None: None.
    """
    request_host=request.host
    output = "<html><title>Crop Rows Generator (CRG) - API v1.0 </title><head>"
    output += "<link rel='stylesheet' type='text/css' href='css/style.css'>"
    output += "<link rel='stylesheet' type='text/css' href='css/tabs.css'>"
    output += "<script src='js/tabs.js'></script>"
    output += "</head><body>" 
    output += "<h2>CROP ROWS GENERATOR (CRG) - API</h2>"
    output += "<h3>Version: 1.0</h3>"
    output += "<h4>Crop Rows Generator CLI - <i>is Running on server:</i> <span style='color:red;'>http://"+request_host+"</span></h4>"
    output += "Crop Rows-API exposes the Crop Rows-CLI infrastructure via a standardized programmatic interface. The Crop Rows API is a RESTful API based on HTTPS requests and JSON responses."
    output += "<br><br>"

    output += "<div class='tab'>"
    output += "<button class='tablinks' onclick='openTabByID(event,1)' id='defaultOpen' >API Usage</button>"
    output += "<button class='tablinks' onclick='openTabByID(event,2)'>Server Info</button>"
    output += "</div>"

    output += "<div id='tab_1' class='tabcontent'>"
    output += "<h3>API Usage:</h3>"
    output += "<table class='zui-table' style='width:100%'><thead><tr><th>METHOD</th><th>URL</th><th>Response</th></tr></thead>"
    output += "<tr><td>GET</td><td>http://"+request_host+"/imlive</td><td>Crop Rows API Status (JSON)</td></tr>"
    output += "<tr><td>GET</td><td>http://"+request_host+"/os</td><td>OS information (JSON)</td></tr>"
    output += "<tr><td>GET</td><td>http://"+request_host+"/croprows/<b>croprows-projectfile.xml</b></td><td>Execute Crop Rows processing task for <b>croprows-projectfile.xml</b> </td></tr>"
    output += "<tr><td>POST</td><td>http://"+request_host+"/crimageuploader/</td><td>@image=filename.tif <br><br><b>Example:</b><br><br> curl -i -X POST \"Content-Type: multipart/form-data\" \<br><span class='tabspace'></span>-F \"image=@uploadfile.tif\" http://"+request_host+"/crimageuploader</td></tr>"
    output += "<tr><td>POST</td><td>http://"+request_host+"/crmaskuploader/</td><td>@shp=file.shp, @shx=file.shx, @dbf=file.dbf <br><br><b>Example:</b><br><br> curl -i -X POST \"Content-Type: multipart/form-data\" \<br><span class='tabspace'></span>-F \"shp=@filemask.shp\" \<br><span class='tabspace'></span>-F \"shx=@filemask.shx\" \<br><span class='tabspace'></span>-F \"dbf=@filemask.dbf\" http://"+request_host+"/crmaskuploader</td></tr>"
    output += "</table>"
    output += "</div>"

    response = requests.get("http://"+request_host+"/os")
    jsonresponse = json.loads(response.text)


    output += "<div id='tab_2' class='tabcontent'>"
    output += "<h3>Server Staus (<span style='color:red;'>Ready</span>)</h3>"
    output += "<p><ul>"
    output += "<li><b>Hardware Platform:</b> <span id='hardware_platform'>"+jsonresponse["hardware_platform"]+"</span></li>"
    output += "<li><b>Operating System:</b> <span id='operating_system'>"+jsonresponse["operating_system"]+"</span></li>"
    output += "<li><b>Kernel:</b> <span id='kernel'>"+jsonresponse["kernel"]+"</span></li>"
    output += "<li><b>Kernel Version:</b> <span id='kernel_version'>"+jsonresponse["kernel_version"]+"</span></li>"
    output += "<li><b>Release:</b> <span id='release'>"+jsonresponse["release"]+"</span></li>"
    output += "<li><b>Machine:</b> <span id='machine'>"+jsonresponse["machine"]+"</span></li>"
    output += "<li><b>Node Name:</b> <span id='node_name'>"+jsonresponse["node_name"]+"</span></li>"
    output += "<li><b>Num Processors:</b> <span id='nproc' style='color:red;'><b>"+jsonresponse["nproc"]+"</b></span></li>"
    output += "<li><b>Processor:</b> <span id='processor'>"+jsonresponse["processor"]+"</span></li>"
    output += "<li><b>Pwd:</b> <span id='pwd'>"+jsonresponse["pwd"]+"</span></li>"
    output += "<li><b>Whoami:</b> <span id='whoami'>"+jsonresponse["whoami"]+"</span></li>"
    output += "<li><b>Shared Folder Size:</b> <span id='foldersize'>"+jsonresponse["foldersize"]+"</span></li>"
    output += "</ul></p>"
    output += "</div>"
    output += "<hr>"

    output += "<script>"
    output += "document.getElementById('defaultOpen').click();"
    output += "</script>"

    output += "<p><b>CRG - API</b> is part of <b>AN AUTOMATIC CROP ROWS GENERATOR USING AERIAL HIGH-RESOLUTION IMAGES FOR PRECISION AGRICULTURE</b> Master thesis."
    output += "<br>In partial fulfillment of the requirements for the degree of: "
    output += "Master in Engineering with a Major in Computer Science</p>"
    output += "<br><div>"
    output += "<div class='box-inline-block'>"
    output += "<b>Researcher</b><br>- Fabio Andres Herrera - fabio.herrera@correounivalle.edu.co<br>"
    output += "<br><b>Supervisors</b><br>- Maria Patricia Trujillo, Ph.D"
    output += "<br>- Ivan Mauricio Cabezas, Ph.D"
    output += "</div></div>"
    output += "<p><br><b>Multimedia and Computer Vision Research Group (MMV-LAB)</b>"
    output += "<br>Universidad del Valle / Santiago de Cali"
    output += "<br>Colombia - 2018</p>"
    output += "</body></html>"
    return output

@app.route('/imlive',methods=['GET'])
def imlive():
    """
    imlive. Obtain server status
       
    :returns None: None.
    """
    return jsonify({'api':'croprows api 1.0','cli':'croprows cli 1.0','alive': 'true'})

@app.route('/os',methods=['GET'])
def osInfo():
        """
        osInfo. Obtain server info
        
        :returns None: None.
        """
        if get_platform()=='Windows':
            return 'Request not supported in Windows platforms' 
        else:
            kernel = subprocess.check_output(['uname','-s'])
            release = subprocess.check_output(['uname','-r'])
            nodename = subprocess.check_output(['uname','-n'])
            kernelv = subprocess.check_output(['uname','-v'])
            machine = subprocess.check_output(['uname','-m'])
            processor = subprocess.check_output(['uname','-p'])
            os = subprocess.check_output(['uname','-o'])
            hardware = subprocess.check_output(['uname','-i'])
            path = subprocess.check_output(['pwd'])
            processingunits = subprocess.check_output(['nproc'])
            whoami = subprocess.check_output(['whoami'])
            foldersize = subprocess.check_output(['du','-sh','orthomosaics'])  
            return jsonify({'kernel': kernel,
                            'release': release,
                            'node_name': nodename,
                            'kernel_version': kernelv,
                            'machine': machine,
                            'processor': processor,
                            'operating_system': os,
                            'hardware_platform': hardware,
                            'pwd': path,
                            'nproc': processingunits,
                            'whoami': whoami,
                            'foldersize': foldersize})

@app.route('/croprows/<string:paramfile>',methods=['GET'])
def indexw(paramfile):
    """
    indexw. Start processing task
        
    :param paramfile: (string) file to process.
    :returns None: None.
    """
    filetoprocess = paramfile
    def inner():
        proc = subprocess.Popen(
            ['croprows-cli/crg_cli.sh '+filetoprocess],
            shell=True,
            stdout=subprocess.PIPE
        )
        output = "<html><title>Crop Rows Generator - API v1.0 </title><head>"
        output += "<link rel='stylesheet' type='text/css' href='../css/styleprocessing.css'>"
        output += "</head><body>" 
        output += "<h3>CROP ROWS GENERATOR - CLI v1.0<h3>"
        output += "<h3>Executing CropRows processing task for: <span style='color:red;'>" + filetoprocess + " </span> file </h3>"
        yield output
        yield '<pre>'
        for line in iter(proc.stdout.readline,''):
            yield unescape(line.rstrip())+'\n'
            #yield '<pre>'+line.rstrip() + '</pre>'
        yield '</pre>'
    return Response(inner(), mimetype='text/html')

def unescape(s):
    s = s.replace("[0;31;40m[->][0m", "<span>[->]</span>")
    s = s.replace("[6;30;42m[DONE][0m", "<span style='color:green'><b>[DONE]</b></span>")
    s = s.replace("[6;30;46m[*][0m", "<span style='color:green'>[*]</span>")
    s = s.replace("[6;30;41m[-][0m", "<span style='color:red'>[-]</span>")
    s = s.replace("[0;31;40m[WORKER][0m", "<span style='color:blue'>[WORKER]</span>")
    s = s.replace("[0;30;41m[ERROR][0m", "<span style='color:red'>[ERROR]</span>")
    s = s.replace("[0;30;41m[FAIL][0m", "<span style='color:red'>[FAIL]</span>")
    s = s.replace("[6;30;43m[CHECK][0m", "<span style='color:yellow'>[CHECK]</span>")
    s = s.replace("[ module loaded ]", "<span style='color:red'><b>[ module loaded ]</b></span>")
    s = s.replace("[0;32;44m[####][0m", "<span style='color:#FF00EF;'><b>[####]</b></span>")
    return s


@app.route("/crimageuploader", methods=['POST'])
def uploadimagefile():
    file = request.files['image']
    f = app.config['UPLOAD_FOLDER']+'/'+file.filename
    file.save(f)
    return 'CropRows API upload image file done !'

@app.route("/crmaskuploader", methods=['POST'])
def uploadmaskfile():
    fileshp = request.files['shp']
    fileshx = request.files['shx']
    filedbf = request.files['dbf']
    f1 = app.config['UPLOAD_FOLDER']+'/'+fileshp.filename
    f2 = app.config['UPLOAD_FOLDER']+'/'+fileshx.filename
    f3 = app.config['UPLOAD_FOLDER']+'/'+filedbf.filename
    fileshp.save(f1)
    fileshx.save(f2)
    filedbf.save(f3)
    return 'CropRows API upload mask file done !'

if __name__ == '__main__':
        app.run(debug = True, host='0.0.0.0', port='2767')
