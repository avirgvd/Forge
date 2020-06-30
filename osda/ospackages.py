# -*- coding: utf-8 -*-
###
# Copyright 2020 Hewlett Packard Enterprise
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###

import json
import osda.geniso as geniso
import osda.config as config
import logging

ospackages_settings = []

def init():


    fin = open('/opt/hpe/osda/data/config/ospackages.json', 'r')
    global ospackages_settings
    ospackages_settings = json.load(fin)
    #print(ospackages_settings)
    fin.close()

def getSupportedOSList():
    return ["ESXi7", "ESXi6", "RHEL7", "RHEL8"]

def getOSPackageById(id):

    logging.debug("getOSPackage")
    global ospackages_settings

    for package in ospackages_settings:
        logging.debug(package)
        if package['uri'] == id:
            return package

    return []

def getOSPackages():

    global ospackages_settings

    return ospackages_settings

def getOSPackagesStats():

    total = len(ospackages_settings)

    stats = dict()

    for package in ospackages_settings:
        logging.debug(package)
        if package['osType'] in stats:
            stats[package['osType']] += 1 
        else:
            stats[package['osType']] = 1
    statsJSON = []
    for key in stats.keys():
        statsJSON.append({ "osType": key, "count": stats[key]})

    return ({ "total": total, "stats": statsJSON})
        

def getOSPackage(ospackagename):
    logging.info("getOSPackage: ospackagename: " + ospackagename)
    fin = open('/opt/hpe/osda/data/config/ospackages.json', 'r')
    global ospackages_settings
    ospackages_settings = json.load(fin)
    fin.close()
    ospackage = {}
    for ospack in ospackages_settings:
        if ospack['package'] == ospackagename:
            ospackage = ospack
            break


    logging.info("#################### " + json.dumps(ospackage))
    if ospackage == {}:
        logging.error("The requested OS package is not found for: " + ospackagename)
        err =  ("Invalid or unknown OS package -" + ospackagename + " specified. Cannot proceed")
        raise Exception(err)

    return ospackage

def setOSPackage(ospackagedata):

    logging.debug("setOSPacage: ")
    logging.debug(ospackagedata)
    global ospackages_settings
    ospackages_settings.append(ospackagedata)
    logging.debug("ospackages: ")
    logging.debug( ospackages_settings)

    fout = open('/opt/hpe/osda/data/config/ospackages.json', 'w')
    json.dump(ospackages_settings, fout)
    fout.close()

def createOSPackage(ospackagedata, orig_iso_path):
    global ospackages_settings


    logging.debug("createOSPackage: Generating OS package for: ")
    logging.debug(ospackagedata)
    #print(type(ospackagedata))

    ospackitem = json.loads('{ "uri": "", "package": "", "osType":  "", "ISO_http_path": "" }')

    logging.debug("%%%%%%%%%%%%%")
    logging.debug(ospackitem['package'])
    ospackitem['uri'] = uuid.uuid4().hex
    ospackitem['package'] = ospackagedata['ospackage']
    ospackitem['osType'] = ospackagedata['ostype']

    target_dir = config.WalkmanSettings().get("local_http_root")

    if ospackitem['osType'] == 'ESXi6':
        target_iso_path = geniso.createKickstartISO_ESXi67(orig_iso_path, target_dir)
        logging.info("createOSPackage: target_iso_path: " + str(target_iso_path))
        ospackitem['ISO_http_path'] = target_iso_path.split(target_dir)[1]
        setOSPackage(ospackitem)
        return ospackitem

    return {"error": "Unsupported OS type"}


if __name__ == '__main__':
    print("sdsds")


    init()



    package = getOSPackage("junkos")
    print(package)
