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

from pprint import pprint
from hpOneView.oneview_client import OneViewClient
from hpOneView.exceptions import HPOneViewException

import json
import threading
import random
import socket

import os
import uuid
import re
import time
import datetime
import logging

import osda.config as config
import osda.ospackages as ospackages
import osda.geniso  as geniso
import osda.rhelgeniso as rhelgeniso
import osda.ilodeployment as ilodeployment
import osda.ilodeploymentgen9 as ilodeploymentgen9
import osda.synergydeployment as synergydeployment


# You can use username/password or sessionID for authentication.
# Be sure to inform a valid and active sessionID.
osActivitiesConfig = config.Activities()

walkman_settings = {}
#ksfiles_settings = {}
#ospackages_settings = []


def init(hostname):
    try:
        # Set up cert directory and config directory if not present
        directories = ['/opt/hpe/osda/data/config', '/opt/hpe/osda/data/certs']
        for directory in directories:
            if not os.path.exists(directory):
                os.mkdir(directory)
        
        # Check for the default config files. Create new config with its default contents if file does not exists.
        defaultConfigs ={
            '/opt/hpe/osda/data/config/ksfiles.json' : '[]',
            '/opt/hpe/osda/data/config/ksfiles.json' : json.dumps([
                    {
                        "osType": "ESXi6",
                        "basekspath": "/opt/hpe/osda/data/kickstarts/esxi67/ks.cfg"
                    },
                    {
                        "osType": "ESXi7",
                        "basekspath": "/opt/hpe/osda/data/kickstarts/esxi70/ks.cfg"
                    },
                    {
                        "osType": "RHEL7",
                        "basekspath": "/opt/hpe/osda/data/kickstarts/rhel76/ks.cfg"
                    }]),
            '/opt/hpe/osda/data/config/networks.json' : '[]',
            '/opt/hpe/osda/data/config/ospackages.json' : '[]',
            '/opt/hpe/osda/data/config/ovappliances.json' : '[]',
            '/opt/hpe/osda/data/config/walkman.json' : json.dumps({
                "ov_certs_path": "/opt/hpe/osda/data/certs",
                "temp_dir": "/tmp",
                "ks_basedir": "/opt/hpe/osda/data/kickstarts", 
                "http_server": "local", 
                "local_http_root": "/var/www/html/", 
                "http_file_server_url": "http://127.0.0.1/"})
        }
        for configFile, defaultContent in defaultConfigs.items():
            if not os.path.exists(configFile):
                with open(configFile, 'w') as newFile:
                    newFile.write(defaultContent)
        
        config.WalkmanSettings().set("http_file_server_url", "http://" + hostname + "/")

    #    fin = open('../config/ksfiles.json', 'r')
    #    global ksfiles_settings 
    #    ksfiles_settings = json.load(fin)
    #    #print(ksfiles_settings)
    #    fin.close()

    #    fin = open('../config/ospackages.json', 'r')
    #    global ospackages_settings
    #    ospackages_settings = json.load(fin)
    #    print(ospackages_settings)
    #    fin.close()

        ospackages.init()

        synergydeployment.init()
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getDashboardData():
    try:
        #ovcount = len(ov_appliances)
        ovcount = synergydeployment.getOVCount()
        osPackagesStats = ospackages.getOSPackagesStats()

        return ({ "ovCount": ovcount, "osPackages": osPackagesStats})
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getOSPackageById(id):
    try:
        return ospackages.getOSPackageById(id)
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getOSPackages():
    try:
        return ospackages.getOSPackages()
    except Exception as err:
        logging.exception(err)
        raise Exception from err


# TASK is any long running operation that runs asynchrously as a thread/process
# Each long running task shall be assigned with TASKID so that the caller can
# poll for the task status using this identifier

# Tasks lookup table for storing task progress
# Lookup this table using TASKID for querying task progress information


def getTaskStatus(taskid):
    '''
    The overall task status should be either Running, Success, or Fail
    The subtask status should be either Error, Complete, or In-Progress
    '''
    try:
        taskStatus = osActivitiesConfig.getTaskStatus(taskid)
        logging.debug(f"Task[{taskid}]: {taskStatus}")
        overallProgress = 0
        totalTasks = subTasksToComplete = len(taskStatus["subTasks"])
        subTasksError = 0
        failedHosts = []
        for subTask in taskStatus["subTasks"]:
            logging.debug(f"{subTask['hostName']} progress: {subTask['progress']}, status: {subTask['status']}")
            overallProgress += subTask["progress"]
            if subTask["status"].lower() == "complete" or subTask["status"].lower() == "error":
                subTasksToComplete -= 1
                if subTask["status"].lower() == "error":
                    subTasksError += 1
                    failedHosts.append(subTask["hostName"])
        taskStatus['progress'] = round(overallProgress / totalTasks)
        if subTasksToComplete == 0 and subTasksError == 0:
            taskStatus["status"] = "Success"
        elif subTasksToComplete == 0 and subTasksError > 0:
            taskStatus["status"] = "Fail"
            failedHosts = ", ".join(failedHosts)
            errorMsg = f"Task {taskid} failed. Total {subTasksError} hosts failed to deploy: {failedHosts}"
            taskStatus["errorMsg"] = errorMsg
        return taskStatus
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getSupportedOSList():
    try:
        #return config.OSPackage().getSupportedOSList()
        return ospackages.getSupportedOSList()
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getAllTasks():
    try:
        return osActivitiesConfig.getAllTasks()
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getOVAppliance(ovalias):
    try:
        return synergydeployment.getOVAppliance(ovalias)
    except Exception as err:
        logging.exception(err)
        raise Exception from err


def getRegisteredOVs():
    try:
        return synergydeployment.getRegisteredOVs()
    except Exception as err:
        logging.exception(err)
        raise Exception from err

#TODO: add validation implementation
def validateDeployData(deployData):
    try:
        logging.debug(deployData)
        return 0
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def deployMain(deployData):
    try:
        logging.debug("deployMain: deployData: ")
        logging.debug(deployData)

        validationresult = validateDeployData(deployData)

        if(validationresult != 0):
            return({"result": {},  "error": "Data validation failed. Check your inputs"})

        #taskID = generateTaskID()
        #taskID = createTask(deployData)
        taskID = osActivitiesConfig.createTask(deployData)

        #return ({"result": { "taskID": taskID}, 'error': {}})

        # thread function for each deployment method
        threadfunction = ""
        if(deployData['deploymentMode'] == "hpeilo"):
            logging.info("HPE iLO based deployment for Gen10 servers")
            #threadfunction = deployByILO_Th;
            ilodeployment.deployByILO(osActivitiesConfig, taskID, deployData)

        elif(deployData['deploymentMode'] == "hpesynergy"):
            logging.info("HPE OneView based deployment")
            #threadfunction = deployByOneView_Th;
            synergydeployment.deployByOneView(taskID, deployData)

        elif(deployData['deploymentMode'] == "hpeilo_gen9"):
            logging.info("HPE iLO based deployment for Gen9 servers")
            ilodeploymentgen9.deployByILO(osActivitiesConfig, taskID, deployData)

        else:
            logging.info("Unsupported deployment method")
            errMsg = "Unsupported deployment method [" + deployData['deploymentMode'] + "] specified"
            return({"result": {}, "error": errMsg})
        
        #deploy_bg = threading.Thread(target=threadfunction, args=(deployData, taskID))
        #deploy_bg.start()
        #return TasksTable
        #return ({"result": "Test", "TaskID": taskID})
        return ({"result": { "taskID": taskID}, 'error': {}})
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def registerOV(ovdetails):

    try:
        ov_entry =  synergydeployment.registerOV(ovdetails)
        return ({"result": "success", "error": {}})
    except Exception as err:
        return ({"result": "error", "error": {"message": str(err)}})
        

def getSPTs(ovalias):
    try:
        return synergydeployment.getSPTs(ovalias)
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getILONetworkConnections(iloip, ilocreds, gen="Gen10"):
    try:
        if gen == "Gen10": 
            return ilodeployment.getILONetworkConnections_ex(iloip, ilocreds['user'], ilocreds['password'])
        elif gen == "Gen9": 
            return ilodeploymentgen9.getILONetworkConnections_ex(iloip, ilocreds['user'], ilocreds['password'])
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getILOStorageDrives(iloip, ilocreds, gen="Gen10"):
    try:
        if gen == "Gen10": 
            return ilodeployment.getILOStorageDrives_ex(iloip, ilocreds['user'], ilocreds['password'])
        elif gen == "Gen9": 
            return ilodeploymentgen9.getILOStorageDrives_ex(iloip, ilocreds['user'], ilocreds['password'])
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getOVSPTNetworkConnections(ovname, sptname):
    try:
        return synergydeployment.getOVSPTNetworkConnections(ovname, sptname)
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getOVSPTStorageDrives(ovname, sptname):
    try:
        return synergydeployment.getOVSPTStorageDrives(ovname, sptname)
    except Exception as err:
        logging.exception(err)
        raise Exception from err

def getURLforOSPackage(OSPackage):
    try:
        basehttpurl = config.WalkmanSettings().get("http_file_server_url")

        ospackagedata = ospackages.getOSPackage(OSPackage)

        if ospackagedata != {}:
            return basehttpurl + ospackagedata['ISO_http_path']
        else:
            return ""
    except Exception as err:
        logging.exception(err)
        raise Exception from err


def createOSPackage(ospackagedata, orig_iso_path):
    try:
        logging.info("createOSPackage: Generating OS package for: ")
        logging.info(ospackagedata)

        ospackitem = json.loads('{ "uri": "", "package": "", "osType":  "", "ISO_http_path": "" }')

        ospackitem['uri'] = uuid.uuid4().hex
        ospackitem['package'] = ospackagedata['name']
        ospackitem['osType'] = ospackagedata['osType']

        target_dir = config.WalkmanSettings().get("local_http_root")
        
        if ospackitem['osType'] == 'ESXi6':
            target_iso_path = geniso.createKickstartISO_ESXi67(orig_iso_path, target_dir)
            logging.info("createOSPackage: target_iso_path: " + str(target_iso_path))
            ospackitem['ISO_http_path'] = target_iso_path.split(target_dir)[1]
            ospackages.setOSPackage(ospackitem)
            return { "result": ospackitem, "error": ""}
        elif ospackitem['osType'] == 'ESXi7':
            target_iso_path = geniso.createKickstartISO_ESXi67(orig_iso_path, target_dir)
            logging.info("createOSPackage: target_iso_path: " + str(target_iso_path))
            ospackitem['ISO_http_path'] = target_iso_path.split(target_dir)[1]
            ospackages.setOSPackage(ospackitem)
            return { "result": ospackitem, "error": ""}
        elif ospackitem['osType'] == 'RHEL7':
            target_iso_path = rhelgeniso.createKickstartISO_RHEL76(orig_iso_path, target_dir)
            logging.info("createOSPackage: target_iso_path: " + str(target_iso_path))
            ospackitem['ISO_http_path'] = target_iso_path.split(target_dir)[1]
            ospackages.setOSPackage(ospackitem)
            return { "result": ospackitem, "error": ""}

        return {"result": {}, "error": "Unsupported OS type"}
    except Exception as err:
            logging.exception(err)
            raise Exception from err

def getNetworks():
    try:
        fin = open('/opt/hpe/osda/data/config/networks.json', 'r')
        networks = json.load(fin)
        fin.close()

        return networks
    except Exception as err:
            logging.exception(err)
            raise Exception from err

def addNetwork(network):
    try:
        if not network:
            raise Exception('Empty network information')
        fin = open('/opt/hpe/osda/data/config/networks.json', 'r')
        networks = json.load(fin)
        fin.close()

        for networkitem in networks:
            if networkitem['name'] == network['name']:
                errMsg = "A network with name " + network['name'] + "already exists"
                logging.error(errMsg)
                return { 'error': errMsg, 'result': "fail"}
                

        networks.append(network)
        fout = open('/opt/hpe/osda/data/config/networks.json', 'w')
        json.dump(networks, fout)
        fout.close()

        return {'error': "", 'result': "success"}
    except Exception as err:
            logging.exception(err)
            raise Exception from err

def getNetwork(networkname):
    try:

        fin = open('/opt/hpe/osda/data/config/networks.json', 'r')
        networks = json.load(fin)
        fin.close()

        for network in networks:
            logging.debug(network)
            if network['name'] == networkname:
                return { "result": network, "error": ""}

        return { "result": {}, "error": "Requested deployment network NOT found "}
    except Exception as err:
            logging.exception(err)
            raise Exception from err

if __name__ == '__main__':

    print("main")
 #   ilocreds = {"user": "v241usradmin", "password": "HP!nvent123"}
  #  getILONetworkConnections("10.188.1.184", ilocreds )

  #  init("10.188.210.14")

    #taskID = createTask(3)
   # print("########################################")
    #print(TasksTable)
    #print("########################################")
    #setTaskStatus(taskID, 0, "Completed")

    init("10.188.210.14")

    ovconfig = getOVConfig("syn0210")
    oneview_client = oneviewConnect(ovconfig)
    spdata = oneview_client.server_profiles.get_by_name("sp21")

    OSConfigJSON = json.loads('{"mgmtNIC": {"connectionName": "vmnic0"}, "osDrive": {"driveName": "localosdrive"}, "networkName": "testnetwork", "netmask": "255.255.255.0", "vlan": "210", "gateway": "10.188.210.1", "dns1": "10.188.0.2", "dns2": "10.188.0.3", "ipAddr": "10.188.210.45", "bootProto": "static", "hostName": "host45", "serverProfile": "sp21", "osPackage": "VMware-ESXi-6.7.0-Update3-15160138-HPE-Gen9plus-670.U3.10.5.0.48-Dec2019.iso", "id": 0, "progress": 4, "status": "In-Progress", "startTime": ["2020-04-12T01:45:56.261634"], "message": "Created the server profile: sp45"}') 

    replacedData = replaceWithSPData(oneview_client, OSConfigJSON, spdata) 
    print("Replaced data: ")
    print(replacedData)


    #genOVCert(ovdetails)

    #getOVSPTNetworkConnections("Synergy210", "SPT-ESXi")

    #createOSPackage({'ospackage': 'esxi12', 'ostype': 'ESXi6.7'}, "/tmp/VMware-ESXi-6.7.0-9484548-HPE-Gen9plus-670.10.3.5.6-Sep2018.iso")
