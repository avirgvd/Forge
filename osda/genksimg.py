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


import os
import string
import subprocess
import json
import tempfile
import uuid
import osda.config as config
import logging
#import ospackages

defaultConfig = config.DefaultConfig()
ksBaseImg = defaultConfig.ksBaseImg

###################################################################
#This function to modify KS file to update hostname, ipaddress..etc
###################################################################

def modifyKSFile(baseKSFile, targetKSFile, OSConfigJSON):

    if "kickstartFile" in OSConfigJSON and OSConfigJSON['kickstartFile'] != "":
        # If user defined kickstart is present then append the filename to baseKS path
        ksfile_name = os.path.dirname(baseKSFile) + os.pathsep + OSConfigJSON['kickstartFile']
    else:
        ksfile_name = baseKSFile

    ks_fopen = open(ksfile_name).read()

    ks_fopen = ks_fopen.replace('%HOSTNAME%', OSConfigJSON['hostName'])

    networks = OSConfigJSON['networks']

    ks_fopen = ks_fopen.replace('%IPADDR1%', networks[0]['ipAddr'])
    ks_fopen = ks_fopen.replace('%MAC11%', networks[0]['NIC1']['macAddress'])
    if "NIC2" in networks[0] and "macAddress" in networks[0]['NIC2']: 
        ks_fopen = ks_fopen.replace('%MAC12%', networks[0]['NIC2']['macAddress'])
    ks_fopen = ks_fopen.replace('%DNS11%', networks[0]['dns'].strip())
    ks_fopen = ks_fopen.replace('%NETMASK1%', networks[0]['netmask'])
    ks_fopen = ks_fopen.replace('%GATEWAY1%', networks[0]['gateway'])
    if "vlans" in networks[0]: 
        ks_fopen = ks_fopen.replace('%VLANS1%', networks[0]['vlans'])

    # Second network is optional so check if it exists first 
    if networks[1]:
        ks_fopen = ks_fopen.replace('%IPADDR2%', networks[1]['ipAddr'])
        ks_fopen = ks_fopen.replace('%MAC21%', networks[1]['NIC1']['macAddress'])
        if "NIC2" in  networks[1] and "macAddress" in networks[1]['NIC2']:
            ks_fopen = ks_fopen.replace('%MAC22%', networks[1]['NIC2']['macAddress'])
        ks_fopen = ks_fopen.replace('%DNS21%', networks[1]['dns'].strip())
        ks_fopen = ks_fopen.replace('%NETMASK2%', networks[1]['netmask'])
        ks_fopen = ks_fopen.replace('%GATEWAY2%', networks[1]['gateway'])
        if "vlans" in networks[1]: 
            ks_fopen = ks_fopen.replace('%VLANS2%', networks[1]['vlans'])

    if "driveID" in  OSConfigJSON['osDrive']:
        ks_fopen = ks_fopen.replace('%DRIVEID%', OSConfigJSON['osDrive']['driveID'].lower())

    ks_fopenW = open(targetKSFile, 'w')
    ks_fopenW.write(ks_fopen)
    ks_fopenW.close()


def modifyKSFileEsxi(baseKSFile, targetKSFile, OSConfigJSON):
   
    ksfile_name = os.path.basename(baseKSFile).split('.',1)[0] + '.cfg'
    ks_fopen = open(baseKSFile).read()

    ks_fopen = ks_fopen.replace('%KSHOSTNM%', OSConfigJSON['hostName'])
#    ks_fopen = ks_fopen.replace('%KSROOTPW%', OSConfigJSON['rootPWD'])

    # Comment/uncomment appropriate line in KS based on bootproto = dhcp or static
    if OSConfigJSON['bootProto'] == "dhcp":
         ks_fopen = ks_fopen.replace('%DHCP%', "")
         ks_fopen = ks_fopen.replace('%STATIC%', "#")
    else:
         ks_fopen = ks_fopen.replace('%DHCP%', "#")
         ks_fopen = ks_fopen.replace('%STATIC%', "")

    ks_fopen = ks_fopen.replace('%KSIPADDRESS%', OSConfigJSON['ipAddr'])
    ks_fopen = ks_fopen.replace('%KSNETMASK%', OSConfigJSON['netmask'])
    ks_fopen = ks_fopen.replace('%KSGATEWAY%', OSConfigJSON['gateway'])
    ks_fopen = ks_fopen.replace('%KSDNS1NAME%', OSConfigJSON['dns1'].strip())
    ks_fopen = ks_fopen.replace('%KSDNS2NAME%', OSConfigJSON['dns2'].strip())
    #ks_fopen = ks_fopen.replace('%KSVLAN%', OSConfigJSON['vlan'])
    ks_fopen = ks_fopen.replace('%KSVLAN%', "0")
    ks_fopen = ks_fopen.replace('%KSSYSMAC%', OSConfigJSON['mgmtNIC']['macAddress'])
    if "driveID" in  OSConfigJSON['osDrive']:
        ks_fopen = ks_fopen.replace('%KSDISKINSTALL%', "--drive=naa." + OSConfigJSON['osDrive']['driveID'].lower())
    else:
        ks_fopen = ks_fopen.replace('%KSDISKINSTALL%', "--firstdisk=local")
    #ks_fopenW = open(esxi67KSDir + ksfile_name, 'w')
    ks_fopenW = open(targetKSFile, 'w')
    ks_fopenW.write(ks_fopen)
    ks_fopenW.close()


#    ks_fopen.close()
def modifyKSFileRhel(baseKSFile, targetKSFile, OSConfigJSON):

    ksfile_name = os.path.basename(baseKSFile).split('.',1)[0] + '.cfg'
    ks_fopen = open(baseKSFile).read()

    ks_fopen = ks_fopen.replace('%SYSTEMHOSTNAME%', OSConfigJSON['hostName'])
#    ks_fopen = ks_fopen.replace('%ROOTPSW%', OSConfigJSON['rootPWD'])
    # Comment/uncomment appropriate line in KS based on bootproto = dhcp or static
    if OSConfigJSON['bootProto'] == "dhcp":
         ks_fopen = ks_fopen.replace('%DHCP%', "")
         ks_fopen = ks_fopen.replace('%STATIC%', "#")
    else:
         ks_fopen = ks_fopen.replace('%DHCP%', "#")
         ks_fopen = ks_fopen.replace('%STATIC%', "")
    ks_fopen = ks_fopen.replace('%SYSTEMIP%', OSConfigJSON['ipAddr'])
    ks_fopen = ks_fopen.replace('%SYSTEMNETMASK%', OSConfigJSON['netmask'])
    ks_fopen = ks_fopen.replace('%SYSTEMGW%', OSConfigJSON['gateway'])
    if 'dns2' in OSConfigJSON and 'dns1' in OSConfigJSON:
        ks_fopen = ks_fopen.replace('%SYSTEMNAMESERVER%', OSConfigJSON['dns1'].strip() + ',' + OSConfigJSON['dns2'].strip())
    elif 'dns2' not in OSConfigJSON and 'dns1' in OSConfigJSON:
        ks_fopen = ks_fopen.replace('%SYSTEMNAMESERVER%', OSConfigJSON['dns1'].strip())
    else:
        raise Exception('Missing DNS1 nameserver IP address')
    
    ks_fopen = ks_fopen.replace('%SYSTEMMAC%', OSConfigJSON['mgmtNIC']['macAddress'])
    if "driveID" in  OSConfigJSON['osDrive']:
        ks_fopen = ks_fopen.replace('%KSDISKINSTALL%', OSConfigJSON['osDrive']['driveID'].lower())
    #ks_fopen = ks_fopen.replace('%KSNETDEV%', "vmnic2")

    #ks_fopenW = open(esxi67KSDir + ksfile_name, 'w')
    ks_fopenW = open(targetKSFile, 'w')
    ks_fopenW.write(ks_fopen)
    ks_fopenW.close()
    #ks_fopen.close()


###################################################################
#This function to create IMG file for USB media
###################################################################

#def createKickstartImage(KSPath):
def createKickstartImage(targetksfile, targetksimagefile):

    # There is an empty Image file that should be modified by adding 
    # new ks.cfg to create image file with ks.cfg

    # KSFile, ext=os.path.splitext(imgFileName)
    tempDir = tempfile.TemporaryDirectory()
    logging.info("Temp directory: " + tempDir.name)

    cmd='cp ' + ksBaseImg + ' ' + targetksimagefile
    os.system(cmd)

    #Modify USB Image IMage for new ks file
    cmd = 'kpartx -av '+ targetksimagefile
    cmd_out =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout
    loopDev=str(cmd_out.read().split()[2],'utf-8')

    cmd = 'mount /dev/mapper/' + loopDev + ' ' + tempDir.name
    os.system(cmd)

    # Copy the kickstart file to root of the image mount location
    # The filename of kickstart inside the image should only be ks.cfg
    cmd = 'cp ' + targetksfile + ' ' + tempDir.name + "/ks.cfg"
    os.system(cmd)

    cmd = 'umount ' + tempDir.name 
    os.system(cmd)

    cmd = 'kpartx -d '+ targetksimagefile
    os.system(cmd)
    
    return targetksimagefile


# Returns the http URL for accessing generated image file
#def generateKickStart(baseksfile, targetdir, OSConfigJSON):
def generateKickStart(osType, targetdir, OSConfigJSON):

    logging.debug("generateKickStart: osType: {osType}, targetdir: {target}, " \
                  "osconfigjson: {osCfg}".format(osType=osType, target=targetdir, osCfg=OSConfigJSON));

    # TODO: this function needs implementation
    baseksfile = getBaseKSFile(osType)
    if baseksfile == "":
        logging.exception("Fail to generate kickstart file. Unsupported OS type specified")
        raise Exception("Fail to generate kickstart file. Unsupported OS type specified")

    outksfile = open(baseksfile, 'r')
    # Generate path for new ks.cfg file

    # Generate temp path for server specific ks.cfg
    #newimagefilename = uuid.uuid4().hex + ".img"
    newfilename = uuid.uuid4().hex 
    targetksfile = os.path.join(targetdir, newfilename + ".cfg")
    targetksimagefile = os.path.join(targetdir, newfilename + ".img")

    # Get OS Type from OSPackage name
    #package = ospackages.getOSPackage(OSConfigJSON['osPackage'])
    #print("generateKickStart: osType: " + package['osType'])

    # Generate customized ks.cfg file based on OSConfigJSON data
    modifyKSFile(baseksfile, targetksfile, OSConfigJSON)

#    #if package['osType'] == "ESXi6":
#    if osType == "ESXi6" or osType == 'ESXi7':
#        modifyKSFileEsxi(baseksfile, targetksfile, OSConfigJSON)
#    #if package['osType'] == "RHEL7":
#    if osType == "RHEL7":
#        modifyKSFileRhel(baseksfile, targetksfile, OSConfigJSON)
 
    # Create FAT32 imagefile with the customized ks.cfg in it
    ksimagepath = createKickstartImage(targetksfile, targetksimagefile)

    outksfile.close()

    return ksimagepath

def getBaseKSFile(osType):

    fin = open("/opt/hpe/osda/data/config/ksfiles.json", 'r')
    ksfiles = json.load(fin)
    fin.close()

    for ksfile in ksfiles:
        logging.debug(ksfile)

        if ksfile["osType"] == osType:
            return ksfile["basekspath"]

    return ""



def cleanupKickstartFiles(ksfilepath):

    os.remove(ksfilepath)

    # Remove the file with .cfg extension also
    os.remove(ksfilepath.replace(".img", ".cfg"))

if __name__ == '__main__':

    baseKSFile = getBaseKSFile("ESXi7")
    print("baseKSFile: " + baseKSFile)
    #cleanupKickstartFiles("/var/www/html/4e616a8bdf224eae9f18024c274e7bca.img")


#    generateKickStart("../kickstarts/ksbase/esxi67/ks.cfg", "/root/KSFILES/", osConfigJSON)

    #imgFileT=createKickstartIMG_ESXi67('/root/Walkman/kickstarts/esxi67/ks.cfg')
#    copyToHttp(imgFileT)
