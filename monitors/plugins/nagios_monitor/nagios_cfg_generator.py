import yaml
import os
import ssh.sshutils as ssh
from hostObj import HostObject
from nagios_cfg_gen import NagiosConfigGenUtil

class NagiosConfigGen(object):

    def __init__(self,hostFileName="openstack_config.yaml"):
        abs_path = os.getcwd() + os.sep + 'configs/%s' % hostFileName
        self.hostYamlObj = None
        self.openstack_host_list = []
        self.openstack_vm_list = []
        try:
            fp = open(abs_path)
        except IOError as e:
            print "Error while opening the file...%s" % e
            return

        try:
            self.hostYamlObj = yaml.load(fp)
            #print "self.hostYamlObj: ", self.hostYamlObj, dir(self.hostYamlObj)
        except yaml.error.YAMLError as perr:
            print "Error while parsing...%s" % perr
            return

    def setOpenstackNodeIp(self):
        #print self.hostYamlObj
        for key in self.hostYamlObj.keys():
            ip = self.hostYamlObj[key]["ip"]
            hostname = key
            username = self.hostYamlObj[key]["user"]
            password = self.hostYamlObj[key]["password"]
            role = self.hostYamlObj[key]["role"]
            hstObj = HostObject(hostname,ip,username,password,role,False)
            self.openstack_host_list.append(hstObj)

    def setOpenstackAppVmIp(self,appVmIpFile):
        abs_path = os.getcwd() + os.sep + 'configs/%s' % appVmIpFile
        try:
            fp = open(abs_path)
        except IOError as e:
            print "Error while opening the file...%s" % e
            return
        ipList = fp.readlines()
        fp.close()
        ctr=1
        for ip in ipList:
            hostname = "AppVm-0%s" % str(ctr)
            username = ""
            password = ""
            role = "appvm"
            hstObj = HostObject(hostname,ip.rstrip(),username,password,role,False)
            self.openstack_vm_list.append(hstObj)
            ctr+=1
        print self.openstack_vm_list

    def performNagiosServiceCheck(self):
        for hostObj in self.openstack_host_list:
            ip = hostObj.getIp()
            user = hostObj.getUser()
            pwd = hostObj.getPassword()
            session = ssh.SSH(user,ip,password=pwd)
            output = session.execute('service nrpe status | grep Active: | grep running')
            if output[1] != '':
                print "NRPE running in - %s " % hostObj.getHost()
                hostObj.setNagios(True)
            else:
                print "NRPE is not running in - %s " % hostObj.getHost()
                hostObj.setNagios(False)
    
    def printHostList(self):
        for hostObj in self.openstack_host_list:
            print "%s - %s - %s - %s - %s" % (hostObj.getIp(),hostObj.getHost(),hostObj.getUser(),hostObj.getPassword(),str(hostObj.isNagiosRunning()))
        for hostObj in self.openstack_vm_list:
            print "%s - %s - %s - %s - %s" % (hostObj.getIp(),hostObj.getHost(),hostObj.getUser(),hostObj.getPassword(),str(hostObj.isNagiosRunning()))

    def generateNagiosHostConfig(self):
        for hostObj in self.openstack_host_list:
            if hostObj.isNagiosRunning():
                NagiosConfigGenUtil.generate_nagios_host_config(hostObj.getIp(),hostObj.getHost(),hostObj.getRole())
                #NagiosConfigGenerator.generate_nagios_host_service(hostObj.getIp(),hostObj.getHost()) 

    def generateNagiosAppVmConfig(self):
        for hostObj in self.openstack_vm_list:
            NagiosConfigGenUtil.generate_nagios_appvm_config(hostObj.getIp(),hostObj.getHost(),hostObj.getRole())

if __name__ == '__main__':
    yhp = NagiosConfigGen()
    yhp.setOpenstackNodeIp()
    yhp.performNagiosServiceCheck()
    yhp.generateNagiosHostConfig()
    yhp.setOpenstackAppVmIp("appvmlist")
    yhp.printHostList()
    yhp.generateNagiosAppVmConfig()
  
