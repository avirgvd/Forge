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
import redfish
import time
from redfish.rest.v1 import ServerDownOrUnreachableError
import logging

# Redfish debug logs has bunch of unintended info which
# clutters the log file. Setting the default to 'INFO''
# for now.
#
# TODO: To move this to server code based on user request
logging.getLogger("redfish").setLevel(logging.INFO)

#######################################
# Class for iLO operations 
#######################################

class ILORedfish(object):

    # FIXED REST API based values for POWER
    POWER_OFF = "ForceOff"
    POWER_ON  = "On"
    POWER_RESET = "ForceRestart"
    POWER_PUSH = "PushPowerButton"
    POWER_GRACEFUL_SHUTDOWN = "GracefulShutdown"

    def __init__(self, iloIp, iloUser, iloPassword):
        self.iloUrl = "https://" + iloIp
        self.iloUser = iloUser
        self.iloPassword = iloPassword
        self.phyDrives = None
        self.logicalDrives = None
        self.redfishObj = self.login()

    #######################################
    # Login to the ILO
    #######################################
    def login(self):
        logging.info("ILORedfish: login: " + self.iloUrl)
        try:
            redfishObj = redfish.redfish_client(base_url=self.iloUrl, username=self.iloUser, password=self.iloPassword)
            redfishObj.login()
        except ServerDownOrUnreachableError as excp:
            return "ERROR: server not reachable or does not support RedFish.\n"
        return redfishObj

    #######################################
    # Login to the ILO using SSO URI
    #######################################
    def login_sso(self, iloSSOURL):
        logging.info(iloSSOURL)
        try:
            
            sessionkey='8da7f15a50a2d7e5be42e0c516cf2be05d5d9483754354e89c9af160bb0317c6048b64baaf1d19b77c409134b4a88a29dbc41ca15eb08eb6da5ab135c4495b1c2c4ccd9b8e0cc0fd2be22d08aa87831218755dc0755b01bcb8d6bbc437e949fe0b24176516839ad81b09f6a163bd9a2fc9cd94e807266a44b2a813352729ee0adf3df6de265d4fc98bd338931480760cdff4f7a24894368d9cef8a09693bccae87f5498c28b9bca276c90fd2fa56d7fd2ad02136838e81542be85968baa4db208bceb5ab7c8b1a3f341380663f946ade02341f2742a3fe6e3516bff0509a3f3f7a85334767403ddbc84e7d333944e03b57fc5edc4bde3ccc012cd4a4f57c89e0'
            redfishObj = redfish.redfish_client(base_url='https://10.188.2.2:443', sessionkey=sessionkey)
            redfishObj.login()
        except ServerDownOrUnreachableError as excp:
            return "ERROR: server not reachable or does not support RedFish.\n"
        return redfishObj

    #######################################
    # Logout 
    #######################################
    def logout(self, redfishObj):
        self.redfishObj.logout()
        return "Logout success"

    #######################################
    # Function for get the NetworkAdaperts
    #######################################
    def getILONWAdapters(self):
        logging.info("getILONWAdapters")
        #redfishObj = self.login()
        NetworkAdapters = self.redfishObj.get("/redfish/v1/Systems/1/BaseNetworkAdapters")
        logging.debug("getILONWAdapters 1")
        networkAdaptersList = []
        for member in NetworkAdapters.dict['Members']:
            logging.debug("getILONWAdapters r21")
            adapter = self.redfishObj.get(member["@odata.id"])
            logging.debug("!!!!!!!!!!!!!!!!!!!!!!!!!!!adapter")
            logging.debug(adapter)
            if len(adapter.dict["FcPorts"]) > 0:
                adapterItem = dict()
                adapterItem['adapterId'] = adapter.dict["Id"]
                adapterItem['adapterName'] = adapter.dict["Name"]
                adapterItem['networkPorts'] = adapter.dict["FcPorts"]
                adapterItem['adapterType'] = "HBA"
                adapterItem['structuredName'] = adapter.dict["StructuredName"]
                networkAdaptersList.append(adapterItem)
                #networkAdaptersList.append({"adapterName" : adapterName, "adapterType": adapterType, "structuredName": structuredName, "networkPorts": networkPorts})
            elif len(adapter.dict["PhysicalPorts"]) > 0:
               adapterItem = dict()
               adapterItem['adapterId'] = adapter.dict["Id"]
               adapterItem['adapterName'] = adapter.dict["Name"]
               adapterItem['adapterType'] = "NIC"
               adapterItem['structuredName'] = adapter.dict["StructuredName"]
               networkPorts = []
               for port in adapter.dict["PhysicalPorts"]:
                   macAddress = port["MacAddress"]
                   #if "Status" in port:
                   #     status = port["Status"]["Health"]
                   #else:
                   #     status = "null"
                   networkPorts.append({"macAddress": macAddress, "linkStatus": port['LinkStatus']})

               adapterItem['networkPorts'] = networkPorts
               networkAdaptersList.append(adapterItem)
               #networkAdaptersList.append({"adapterName" : adapterName, "adapterType": adapterType, "structuredName": structuredName, "networkPorts": networkPorts})
        #self.logout(redfishObj)



        logging.debug("##################output")
        logging.debug(json.dumps(networkAdaptersList))
        return networkAdaptersList

    #######################################
    # Function for get the Storage details
    #######################################
    def getILOStorageDrives(self):
        #redfishObj = self.login()
        storageDetails = []
        arrayResponse = self.redfishObj.get("/redfish/v1/Systems/1/SmartStorage/ArrayControllers")
        for ArrayController in arrayResponse.dict["Members"]:
            driveResponse = self.redfishObj.get(ArrayController["@odata.id"])
            if "LogicalDrives" in driveResponse.dict['Links']:
                for drive in (self.redfishObj.get(driveResponse.dict['Links']['LogicalDrives']['@odata.id'])).dict["Members"]:
                    logicalDrive = self.redfishObj.get(drive["@odata.id"])
                    capacityGB = int(logicalDrive.dict["CapacityMiB"])/1024
                    faultTolerance = "RAID " + str(logicalDrive.dict["Raid"])
                    driveName =  logicalDrive.dict["LogicalDriveName"]
                    logicalDriveNumber =  logicalDrive.dict["LogicalDriveNumber"]
                    mediaType =  logicalDrive.dict["MediaType"]
                    VolumeUniqueIdentifier = logicalDrive.dict['VolumeUniqueIdentifier']
                    storageDetails.append({"logicalDriveNumber": logicalDriveNumber, "driveType" : "Logical", "mediaType": mediaType, "capacityGB": capacityGB, 'driveID' : VolumeUniqueIdentifier,  "faultTolerance": faultTolerance})
            if "PhysicalDrives" in driveResponse.dict['Links']:
                for drive in (self.redfishObj.get(driveResponse.dict['Links']['PhysicalDrives']['@odata.id'])).dict["Members"]:
                    physicalDrive = self.redfishObj.get(drive["@odata.id"])
                    capacityGB = physicalDrive.dict["CapacityGB"]
                    name = physicalDrive.dict["Name"]
                    location = physicalDrive.dict["Location"]
                    mediaType = physicalDrive.dict["MediaType"]
                    locationFormat = physicalDrive.dict["LocationFormat"]
                    storageDetails.append({"driveName": name, "driveType" : "physical", "location": location, "LocationFormat" : locationFormat,"mediaType": mediaType,\
					 "capacityGB": capacityGB})
        #self.logout(redfishObj)
        return storageDetails

    #######################################
    # Class for iLO operations             ------   Testing in-progress 
    #######################################
    def mountVirtualMedia(self, mediaUrl, mediaType, bootOnNextServerReset=False):


        logging.info("mountVirtualMedia: mediaUrl: " + mediaUrl)

        #redfishObj = self.login()
        resourceRes = self.redfishObj.get("/redfish/v1/resourcedirectory")
        resourceInstances = resourceRes.dict["Instances"]
        virtualMediaUri = None
        virtualMediaResponse = []
        disableResourceDir = False
        if disableResourceDir or not resourceInstances:
            # if we do not have a resource directory or want to force it's non use to find the
            # relevant URI
            managersUri = self.redfishObj.root.obj['Managers']['@odata.id']
            managersResponse = self.redfishObj.get(managersUri)
            managersMembersUri = next(iter(managersResponse.obj['Members']))['@odata.id']
            managersMembersResponse = self.redfishObj.get(managersMembersUri)
            virtualMediaUri = managersMembersResponse.obj['VirtualMedia']['@odata.id']
        else:
            for instance in resourceInstances:
                # Use Resource directory to find the relevant URI
                if '#VirtualMediaCollection.' in instance['@odata.type']:
                    virtualMediaUri = instance['@odata.id']
        if virtualMediaUri:
            virtualMediaResponse = self.redfishObj.get(virtualMediaUri)
            for virtualMediaSlot in virtualMediaResponse.obj['Members']:
                data = self.redfishObj.get(virtualMediaSlot['@odata.id'])
                if mediaType in data.dict['MediaTypes']:
                    virtualMediaMountUri = data.obj['Actions']['#VirtualMedia.InsertMedia']['target']
                    postBody = {"Image": mediaUrl}
                    virtualMediaEjectUri = data.obj['Actions']['#VirtualMedia.EjectMedia']['target']

                    if mediaUrl:
                        try:
                            self.redfishObj.post(virtualMediaEjectUri, body={})
                            self.redfishObj.post(virtualMediaMountUri, body=postBody)
                        except Exception as err:
                            logging.exception("Unable to mount: {}".format(err))
                            return ({ "result" : "Unable to mount", "error" : err })
                        if bootOnNextServerReset is True:
                            patchBody = {}
                            patchBody["Oem"] = {"Hpe": {"BootOnNextServerReset": \
                                                     bootOnNextServerReset}}
                            bootResp = self.redfishObj.patch(data.obj['@odata.id'], body=patchBody)
                            if not bootResp.status == 200:
                                #logging.exception("Failed to reset the server. Ensure the server is in Power OFF state before deployment")
                                #raise Exception("Failed to reset the server. Ensure the server is in Power OFF state before deployment.")
                                logging.exception("Failed to change one-time boot order to boot into " + mediaType)
                                raise Exception("Failed to change one-time boot order to boot into " + mediaType)


        return

    # This function supports boot device of type logical drive with RAID using local drives
    def modifyBootOrder(self, drive):
        logging.info("modifyBootOrder: drive: " + str(drive))

        #redfishObj = self.login()



        response = self.redfishObj.get("/redfish/v1/Systems/1/BIOS/Boot/Settings/")
        #print(response)
        logging.debug("####################")
        logging.debug(response.obj['PersistentBootConfigOrder'])
        bootOrder = response.obj['PersistentBootConfigOrder']
        logging.debug("####################")
        #print(response.obj['BootSources'])
        bootSources = response.obj['BootSources']


        # First find the matching boot source based on the OS boot drive
        # the matching criteria is, if requested OS drive RAID type matches one of the boot sources
        # and if there are multiple boot sources matching RAID type then look for logical volume number match 
        raidTypeMatch = False
        matchedBootSourceString = ""
 
        for bootSource in bootSources:
            # HPE DL Gen10, boot source has entries with Logical Drive name like "Logical Drive 2"
            # For eg. 'BootString': 'Embedded RAID 1 : HPE Smart Array P816i-a SR Gen10 - 931.4 GiB, RAID1 Logical Drive 2(Target:0, Lun:1
            # But the ilo returns only a numeric for logical drive identifier
            # So look for matching logical drive number 
            logicalDriveName = "Logical Drive " + str(drive['logicalDrive']['logicalDriveNumber'])
            logging.debug("logical drive is: " + logicalDriveName)
            logging.debug("bootSource['BootString'] drive is: " + bootSource['BootString'])
            if logicalDriveName in bootSource['BootString']:
                logging.debug("################## Match found ")
                # If here then both RAID type and logical drive name are matching so this bootSource must be better match
                matchedBootSourceString = bootSource['StructuredBootString']

#            if drive['faultTolerance'].replace(" ", "") in bootSource['BootString']:
#                print("Found!!") 
#                print(str(bootSource))
#                if raidTypeMatch == False:
#                    raidTypeMatch = True
#                    matchedBootSourceString = bootSource['StructuredBootString']
#                else:
#                    print("Duplicate found so try another check")
#                    # Looks like there are mode than 2 logical drives matching RAID mode
#                    # So look for matching logical drive number 
#                    logicalDriveName = "Logical Drive " + str(drive['logicalDriveNumber'])
#                    print("logical drive is: " + logicalDriveName)
#                    print("bootSource['BootString'] drive is: " + bootSource['BootString'])
#                    if logicalDriveName in bootSource['BootString']:
#                        print("##################Match found in duplicates")
#                        # If here then both RAID type and logical drive name are matching so this bootSource must be better match
#                        matchedBootSourceString = bootSource['StructuredBootString']


        logging.info("Matching boot source is: " + matchedBootSourceString)
        bootOrder = response.obj['PersistentBootConfigOrder']
        if matchedBootSourceString == "":
            logging.exception("Unable to find matching boot sources for the requested OS boot device: {}".format(drive))
            raise Exception("Unable to find matching boot sources for the requested OS boot device: " + str(drive))

        # build new boot order first adding the matching boot string to top of the list
        newBootOrder = [matchedBootSourceString]
        for bootEntry in bootOrder:
            if bootEntry != matchedBootSourceString:
                newBootOrder.append(bootEntry)

        # now we have the modified boot order in newBootOrder
        # Now update iLO with new boot order
        body = dict()
        body["PersistentBootConfigOrder"] = newBootOrder
        #body["DefaultBootOrder"] = newBootOrder
        #body = {'DefaultBootOrder': newBootOrder}
        resp = self.redfishObj.patch("/redfish/v1/Systems/1/BIOS/Boot/Settings/", body=body)
        if resp.status != 200:
            logging.info(resp.status)
            logging.error(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))
            logging.exception(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))
            raise Exception("Failed to update boot-order in the iLO")
        else:
            logging.info("Boot order updated successfully to boot from the choosen logical drive")
            logging.info("New BOOT order: {}".format(newBootOrder))


    def changeTemporaryBootOrder(self, boottarget="BiosSetup"):

        systems_members_uri = None
        systems_members_response = None

        #resource_instances = resourceRes = self.redfishObj.get("/redfish/v1/resourcedirectory")
        resourceRes = self.redfishObj.get("/redfish/v1/resourcedirectory")
        resourceInstances = resourceRes.dict["Instances"]

        for instance in resourceInstances:
            if '#ComputerSystem.' in instance['@odata.type']:
                systems_members_uri = instance['@odata.id']
                systems_members_response = self.redfishObj.get(systems_members_uri)

        if systems_members_response:
            logging.debug("\n\nShowing bios attributes before changes:\n\n")
            logging.debug(json.dumps(systems_members_response.dict.get('Boot'), indent=4, sort_keys=True))
        body = {'Boot': {'BootSourceOverrideTarget': boottarget}}
        logging.debug("body: ")
        logging.debug(body)
        resp = self.redfishObj.patch(systems_members_uri, body=body)
        logging.debug("redfishObj.patch returned: ")
        logging.debug(resp.status)

        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                logging.debug(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))
            except Exception as excp:
                logging.error("Setting the boot parameter BootSourceOverrideTarget returned HTTP status 400. Ignoring...")

        elif resp.status != 200:
            logging.error("Setting the boot parameter BootSourceOverrideTarget failed. Ignoring...")
        else:
            logging.debug("\nSuccess!\n")
            logging.debug(json.dumps(resp.dict, indent=4, sort_keys=True))
            if systems_members_response:
                logging.debug("\n\nShowing boot override target:\n\n")
                logging.debug(json.dumps(systems_members_response.dict.get('Boot'), indent=4, sort_keys=True))


    #######################################
    # Function to reboot the server
    #######################################
    def rebootServer(self):
        #redfishObj = self.login()
        resourceRes = self.redfishObj.get("/redfish/v1/resourcedirectory")
        resourceInstances = resourceRes.dict["Instances"]
        for instance in resourceInstances:
            #Use Resource directory to find the relevant URI
            if '#ComputerSystem.' in instance['@odata.type']:
                systems_members_uri = instance['@odata.id']
                systems_members_response = self.redfishObj.get(systems_members_uri)

        if systems_members_response:
            system_reboot_uri = systems_members_response.obj['Actions']['#ComputerSystem.Reset']['target']
            if systems_members_response.obj['PowerState'] == "On":
                logging.error("CRITICAL: Found the server in ON state. CANNOT PROCEED WITH DEPLOYMENT")
            elif systems_members_response.obj['PowerState'] == "Off":
                logging.info("Found the server in OFF state. PROCEEDING WITH DEPLOYMENT")

            try:
                body = dict()
                body['ResetType'] = "On"
                self.redfishObj.post(system_reboot_uri, body=body)
            except Exception as err:
                logging.exception("Failed to restart : {}".format(err))
                return ("Failed to restart", err)
        #self.logout(redfishObj)
        return "Restarted"

    #######################################
    # Function to get iLO power state
    #######################################
    def getPowerState(self):
        iloInfo = self.redfishObj.get('/redfish/v1/Systems/1/')
        return iloInfo.obj['PowerState']

    #######################################
    # Function to set iLO power state
    #######################################
    def setPowerState(self, state):
        iloInfo = self.redfishObj.get('/redfish/v1/Systems/1/')
        resetBody = {}
        if state.lower() == "on":
            resetBody = {"ResetType": self.POWER_ON}

        elif state.lower() == "off":
            resetBody = {"ResetType": self.POWER_OFF}

        elif state.lower() == "push":
            resetBody = {"ResetType": self.POWER_PUSH}

        elif state.lower() == "force-reset":
            resetBody = {"ResetType": self.POWER_RESET}

        elif state.lower() == "graceful-shutdown":
            resetBody = {"ResetType": self.POWER_GRACEFUL_SHUTDOWN}

        response = self.redfishObj.post("/redfish/v1/systems/1/Actions/ComputerSystem.Reset", body=resetBody)
        if response.status != 200:
            logging.exception("Failed to reset power state to {state}: {msg}".format(state=state, msg=response.text))
            raise Exception("Failed to reset power state to {state}: {msg}".format(state=state, msg=response.text))


    #######################################
    # Function to ensure iLO power state
    #
    # If the expected power state is different 
    # from iLO server power state, function will
    # ensure to set the expected power state
    #
    # else, will skip
    #######################################
    def ensurePowerState(self, expectedState):
        state = self.getPowerState()

        if state.lower() != expectedState.lower():
            self.setPowerState(expectedState)
   
    #######################################
    # Function to reset iLO power state
    #
    # If the server state is
    # - Off, func will power on
    # - on, func will force reset
    #######################################
    def resetPowerState(self):
        if self.getPowerState().lower() == "off":
            self.setPowerState("on")
        else:
            self.setPowerState("force-reset")


    #######################################
    # Function to wait for BIOS post to
    # be completed
    #######################################
    def waitForBiosPost(self):
        # Wait for BIOS to be unlocked
        sleepTime = 10
        counter = 25
        while self.isBiosLock():
            counter = counter - 1
            time.sleep(sleepTime)

            if counter == 0:
                # Power off the node and raise Exception
                self.ensurePowerState("graceful-shutdown")
                logging.exception(errorMessage + " : Timeout reach while waiting for BIOS")
                raise Exception(errorMessage + " : Timeout reach while waiting for BIOS")

        # Sleep additional 2 seconds, just to make sure BIOS 
        # updates reflect in redfish
        time.sleep(20)

    #######################################
    # Function to read all physical drives of smart array controllers
    #
    # Populates class attribute 'phyDrives' with list of physical disks
    #######################################
    def physicalDrives(self):
        self.phyDrives = []
        logging.info("Get the list of physical drives")
        for controller in self.redfishObj.get('/redfish/v1/Systems/1/SmartStorage/ArrayControllers').obj["Members"]:
            smartArrayControllerInfo = self.redfishObj.get(controller["@odata.id"] + "/DiskDrives")
            for disk in smartArrayControllerInfo.obj["Members"]:
                driveInfo = {}
                diskInfoObj = self.redfishObj.get(disk["@odata.id"])
                driveInfo["InterfaceType"] = diskInfoObj.obj["InterfaceType"]
                driveInfo["Location"] = diskInfoObj.obj["Location"]
                driveInfo["MediaType"] = diskInfoObj.obj["MediaType"]
                driveInfo["CapacityGB"] = diskInfoObj.obj["CapacityGB"]
                driveInfo["Health"] = diskInfoObj.obj["Status"]["Health"]
                driveInfo["State"] = diskInfoObj.obj["Status"]["State"]
                driveInfo["DiskDriveUse"] = diskInfoObj.obj["DiskDriveUse"]

                self.phyDrives.append(driveInfo)
        return self.phyDrives

    #######################################
    # Function to delete all logical drives
    #######################################
    def deleteAllLogicalDrives(self):
        logging.info("Delete all logical drives")

        logicalDriveReqData = {}
        logicalDriveReqData["DataGuard"] = "Disabled"
        logicalDriveReqData["LogicalDrives"] = []

        smartConfigDeleteSetting = self.redfishObj.put('/redfish/v1/Systems/1/smartstorageconfig/settings', body=logicalDriveReqData)

        if smartConfigDeleteSetting.status != 200:
            logging.exception("Failed to delete RAID configuration")
            raise Exception("Failed to delete RAID configuration")

        # Reset the server to reflect the changes
        self.changeTemporaryBootOrder()
        self.resetPowerState()
        self.waitForBiosPost()

    #######################################
    # Function to create logical drive
    #
    # Returns logical drive or exception
    #######################################
    def createLogicalDrive(self, logicalInputData):
        logging.info("Create logical drive")

        # Read all the physical drives
        self.physicalDrives()
        if not self.phyDrives:
            logging.exception("createLogicalDrive: Failed to create new logical drive: No physical drives present")
            raise Exception("createLogicalDrive: Failed to create new logical drive: No physical drives present")

        # Input parameters for LG creation
        logicalCapacity = int(logicalInputData['capacity'])
        logicalCapacityUnit = logicalInputData['capacityUnit']
        driveTechnology = logicalInputData['driveTechnology']
        deployOperation = logicalInputData['operation']
        raidConfig = logicalInputData['raidLevel']
        doDeletion = False

        errorMessage = "Failed to create logical drive of raid {raid} " \
            "and drive technology {driveTech} with capacity {size} {unit}".format(
            raid=raidConfig, driveTech=driveTechnology, size=logicalCapacity,
            unit=logicalCapacityUnit)
        if deployOperation.upper() == "DELETE_ALL_AND_CREATE".upper():
            doDeletion = True

        if raidConfig.lower() != "raid1":
            logging.exception(errorMessage + " : Only RAID 1 is currently supported")
            raise Exception(errorMessage + " : Only RAID 1 is currently supported")

        if logicalCapacityUnit.upper() == "TB":
            logicalCapacity = logicalCapacity * 1000

        # Get existing logical drives
        existingLogicalDrives = self.getLogicalDrives()
        existingDriveIds = [x['driveID'] for x in existingLogicalDrives]

        # deployOperation can take inputs like "DELETE_ALL_AND_CREATE", "CREATE"
        # By default it is create New, if delete is needed change the REST body
        if doDeletion and existingLogicalDrives:
            self.deleteAllLogicalDrives()

        # Get only unassigned physical drives
        #
        # In case of DELETE_ALL_AND_CREATE, all the physical disk
        # that matches to capacity, drive technology are selected
        unassignedDrives = []
        for drive in self.phyDrives:
            if drive.get('InterfaceType') in driveTechnology and \
               drive.get('MediaType') in driveTechnology and \
               drive.get("CapacityGB") == int(logicalCapacity):

                 if doDeletion:
                      unassignedDrives.append(drive.get("Location"))
                 elif drive.get("DiskDriveUse").lower() == "raw":
                      unassignedDrives.append(drive.get("Location"))

        if not unassignedDrives:
            logging.exception(errorMessage + " : Cannot find raw physical drives")
            raise Exception(errorMessage + " : Cannot find raw physical drives")

        # TODO: print will be debug message
        logging.info("\nList of unassigned drives {} \n".format(unassignedDrives))

        # Map user RAID with redfish RAID level
        RAID_LEVEL = {
            "RAID1": "Raid1",
            "RAID5": "Raid5",
            "RAID10": "Raid10"
        }

        # Future Use: Minimum disk requirements for RAID
        RAID_MIN = {
            "RAID1": 2,
            "RAID5": 3,
            "RAID10": 4
        }

        # TODO: Check if there minimum unassigned drives are avaiable for the raid

        # Request body for LG drive creation
        smartConfigSetting = self.redfishObj.get('/redfish/v1/Systems/1/smartstorageconfig/settings/')
        logicalDriveReqData = smartConfigSetting.obj

        logicalDriveReqData["DataGuard"] = "Disabled"

        logicalDrive = {}
        logicalDrive["LogicalDriveName"] = "LogicalDrive_OSDA"
        logicalDrive["Raid"] = RAID_LEVEL[raidConfig.upper()]
        logicalDrive["DataDrives"] = unassignedDrives[:RAID_MIN[raidConfig.upper()]]
        logicalDriveReqData["LogicalDrives"].append(logicalDrive)

        # Creation of logical drive
        smartConfigUpdateSetting = self.redfishObj.put('/redfish/v1/Systems/1/smartstorageconfig/settings/', body=logicalDriveReqData)
        if smartConfigUpdateSetting.status != 200:
            logging.exception(errorMessage + ": Rest request to create RAID failed : " + smartConfigUpdateSetting.text)
            raise Exception(errorMessage + ": Rest request to create RAID failed : " + smartConfigUpdateSetting.text)

        logging.info ("Raid configuration updated successful. System reset required to reflect the changes")

        # Reset the server to reflect the changes
        self.changeTemporaryBootOrder()
        self.resetPowerState()

        # Wait and check if logical drive is created
        # Wait for maximum of 2 minutes
        #
        # TODO: Need to check for a better logic
        counter = 15
        time.sleep(20)
        sleepTime = 10

        # Wait for BIOS to be unlocked
        self.waitForBiosPost()
        while True:
            newLogicalDrives = self.getLogicalDrives()
            if len(existingLogicalDrives) != len(newLogicalDrives) or doDeletion:
                lgDrive = self.getLogicalDriveFromDisk(newLogicalDrives, unassignedDrives[0])
                if lgDrive and lgDrive['driveID'] not in existingDriveIds:
                    return lgDrive

            if counter == 0:
                # Power off the node and raise Exception
                self.ensurePowerState("graceful-shutdown")
                logging.exception(errorMessage + " : Timeout to find new logical drive")
                raise Exception(errorMessage + " : Timeout to find new logical drive")

            counter = counter - 1
            time.sleep(sleepTime)
        
    #######################################
    # Function to check to get logical drive of a given physical disk
    # 
    # Returns logical drive or None
    #######################################
    def getLogicalDriveFromDisk(self, logicalDriveList, phydrive):
        lgDrive = next((x for x in logicalDriveList if phydrive in x["dataDrives"]), None)
        return lgDrive


    #######################################
    # Function to get logical drives
    #
    # This function re-read all the logical drives
    # even if the logicalDrives are available
    #
    # Populates class attribute 'logicalDrives' with list of logical drives
    #######################################
    def getLogicalDrives(self):
        smartConfigInfo = self.redfishObj.get('/redfish/v1/Systems/1/smartstorageconfig/')
        self.logicalDrives = []
        for lgDrive in smartConfigInfo.obj["LogicalDrives"]:
            drive ={}
            drive["logicalDriveNumber"] = lgDrive["LogicalDriveNumber"]
            drive["dataDrives"] = lgDrive["DataDrives"]
            drive["capacityGiB"] = lgDrive["CapacityGiB"]
            drive["raidLevel"] = lgDrive["Raid"]
            drive["driveID"] = lgDrive["VolumeUniqueIdentifier"]

            self.logicalDrives.append(drive)
        return self.logicalDrives

    #######################################
    # Function to get ilO Post State
    #
    # This function gets the POST state of iLO
    #
    # Post States: Null Unknown Reset PowerOff
    #   InPost InPostDiscoveryComplete FinishedPost 
    #######################################
    def getPostState(self):
        iloInfo = self.redfishObj.get('/redfish/v1/Systems/1/')
        return iloInfo.obj['Oem']['Hpe']['PostState']

    #######################################
    # This function check the right time to
    # updates BIOS
    #
    # Returns true if the post state is
    #   'InPostDiscoveryComplete', 'FinishedPost'
    #
    # Returns False in all other cases
    #######################################
    def isBiosLock(self):
        postState = self.getPostState()
        logging.debug("Post State : {}".format(postState))
        if postState.upper() in ["INPOSTDISCOVERYCOMPLETE", "FINISHEDPOST"]:
            return False

        return True

if __name__ == '__main__':

    SYSTEM_URL = "10.188.2.16"
    LOGIN_ACCOUNT = "v0175usradmin"
    LOGIN_PASSWORD = "HP!nvent123"
    A = ILORedfish(SYSTEM_URL, LOGIN_ACCOUNT, LOGIN_PASSWORD)

    #"BootSourceOverrideTarget@Redfish.AllowableValues": [
    #  "None",
    #  "Pxe",
    #  "Floppy",
    #  "Cd",
    #  "Usb",
    #  "Hdd",
    #  "BiosSetup",
    #  "Utilities",
    #  "Diags",
    #  "UefiTarget",
    #  "SDCard",
    #  "UefiHttp"
    #],
    A.change_temporary_boot_order()


    quit()





    drive = {'logicalDriveNumber': 3, 'faultTolerance': 'RAID 1', 'driveID': '600508B1001CAA4ECFD2FBCFC754E865'}
    A.modifyBootOrder(drive)
    #print (A.getILOStorageDrives())

    #print (A.mountVirtualMedia("http://10.188.210.16/RHEL-7.6-20181010.0-Server-x86_64-dvd1.iso", "CD", bootOnNextServerReset=True))
    #print (A.mountVirtualMedia("http://10.188.210.16/rhelKsImage1.img", "USBStick"))


