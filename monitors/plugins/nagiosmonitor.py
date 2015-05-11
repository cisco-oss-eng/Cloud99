# Service monitor - updates the service status every configured interval
# Service configruations refer 

from pprint import pprint
import urllib2
import json
import base64
import time
import datetime
import ConfigParser
import os
import sys
import ha_engine.ha_infra as infra
from monitors.baseMonitor import BaseMonitor

# ========================== Configurable Parameters ======================
# Ip address based service filter 
# If IP_FILTER is empty all services will be selected else only ip from IP_FILTER considerd for display

# =========================================================================

class NagiosMonitor(BaseMonitor):

    headers = ['host_name', 'description', 'time_critical',
               'time_ok', 'time_indeterminate_nodata']
    polling_interval = 20
    ip_filter = []
    reportDict = {}
    summaryDict = {}
    url = "http://%s:8080/state"
    # path = '/Users/pradeech/HA1/Cloud_HA_Testframework_v1/configs/user_configs/nagios_config.cfg'
    path = os.getcwd() + os.sep + 'configs/user_configs/nagios_config.cfg'

    def stop(self):
        pass

    def report(self):
        pass

    def stable(self):
        pass

    def is_module_exeution_completed(self, finish_exection):
        pass

    def start(self, sync=None, finish_execution=None):

        ip_address = self.get_config('nagios_ip')
        input_args = self.get_input_arguments()
        filterType = str(input_args['nagios']['type'])

        host_config = infra.get_openstack_config()
        #print host_config
        #print "================ "+filterType
        host_filter = []
        if filterType == "node":
            host_filter = self.generateFilterList(host_config,filterType)

        # Execution starts here
        """
        if sync:
            infra.display_on_terminal(self, "Waiting for Runner Notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification from Runner")
        """    
        startTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        ctr = 0
        #while infra.is_execution_completed(self.finish_execution) is False:
        while(finish_execution):
            data = self.getNagiosData(self.url, ip_address)
            self.processAndReport(data,self.reportDict,host_filter,filterType,self.summaryDict) 
            #print self.reportDict
            #self.printServiceStateReport(self.reportDict)
            time.sleep(20)
            # below counter check and break loop will be removed during actual execution
            ctr+=1
            if ctr == 10:
                break
        endTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        #NagiosMonitor.printServiceState(self.reportDict,startTime,endTime)
        NagiosMonitor.writeToFile(self.reportDict,startTime,endTime)
        
    
    #@staticmethod
    def processAndReport(self,data,reportDict,host_filter,filterType,summaryDict):
        #print "================"+filterType
        #print host_filter
        format_string = "%s  |  %s  |  %s  | "
        ret = []
        for ip in data:
            hostService = data[ip]["services"]
            for key in hostService:
                result = {}
                if host_filter != []:
                    if ip in host_filter:
                        #result = NagiosMonitor.createResultDict(data,ip,key)
                        result = self.createResultDict(data,ip,key)
                elif filterType == "openstackvm":
                    if ip.startswith("AppVm-"):
                        #result = NagiosMonitor.createResultDict(data,ip,key)
                        result = self.createResultDict(data,ip,key)
                else:
                    #result = NagiosMonitor.createResultDict(data,ip,key)
                    result = self.createResultDict(data,ip,key)

                if len(result) <= 0:
                    continue

                if result.has_key("output") and len(result["output"]) < 40: # To make multiline
                    ret.append(result)
                else:
                    NagiosMonitor.splitLines(result,ret)
                
                NagiosMonitor.collectFlappingServiceData(ip,key,reportDict,
                            NagiosMonitor.getStatusStr(data[ip]["services"][key]["current_state"]),
                                                        data[ip]["services"][key]["plugin_output"])
                NagiosMonitor.calSummaryReport(ip,key,summaryDict,reportDict,
                            NagiosMonitor.getStatusStr(data[ip]["services"][key]["current_state"]),
                                                         data[ip]["services"][key]["plugin_output"])
            #columns
        #print '-' * 157
        tblLine = '-' * 82
        infra.display_on_terminal(self,tblLine)
        """
        print NagiosMonitor.get_severity_color('INFO', format_string % (
                'Time'.ljust(20),'HostName'.ljust(20),
                "Service Description".ljust(45),
                "Status".ljust(9), "Status Information".ljust(40)))
        print '-' * 160
        """
        infra.display_on_terminal(self,
                NagiosMonitor.get_severity_color('INFO', format_string % (
                'HostName'.ljust(15),
                "Service Description".ljust(45),
                "Status".ljust(9))))
        infra.display_on_terminal(self,tblLine)
        
        #print '-' * 157
        for item in ret:
            if item.get("ip") == " " and item.get("description") == " ":
                #NagiosMonitor.printData(format_string,item)
                self.printData(format_string,item)
                continue
            if host_filter != []: 
                if item.get("ip") in host_filter: 
                    #NagiosMonitor.printData(format_string,item)
                    self.printData(format_string,item)
            elif filterType == "openstackvm": 
                if item.get("ip").startswith("AppVm-"):
                    #NagiosMonitor.printData(format_string,item)
                    self.printData(format_string,item)
            else:
                #NagiosMonitor.printData(format_string,item)
                self.printData(format_string,item)
                
        #print '-' * 157
        infra.display_on_terminal(self,tblLine)

    @staticmethod
    def generateFilterList(hostConfig,filterType):
        filterList = []
        if filterType == 'node':
            for key in hostConfig.keys():
                if hostConfig[key]["role"] == "controller" or hostConfig[key]["role"] == "network" or hostConfig[key]["role"] == "compute":
                    filterList.append(key)
        return filterList             
    
    @staticmethod
    def createResultDict(data,ip,key):
        result = {}
        result["ip"] = ip  # key should be changed into host
        result["description"] = key
        statusStr = NagiosMonitor.getStatusStr(data[ip]["services"][key]["current_state"])
        result["status"] = statusStr
        result["output"] = data[ip]["services"][key]["plugin_output"]
        return result

    @staticmethod
    def updateStatusColor(status,statusDesc):
        if status == "OK":
            return statusDesc
        elif status == "WARNING":
            return NagiosMonitor.get_severity_color("WARNING",statusDesc)
        else:
            return NagiosMonitor.get_severity_color("CRITICAL",statusDesc)

    
    def printData(self,format_string,item):
        #print format_string % (time.ctime(int(time.time())).ljust(25),
        """
        print format_string % (datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S').ljust(20),
                item.get("ip").ljust(20),
                item.get(NagiosMonitor.headers[1])[:40].ljust(45),
                item.get("status").ljust(9),
                item.get("output").ljust(40))
        """
        infra.display_on_terminal(self,format_string % (
                item.get("ip").ljust(15),
                item.get(NagiosMonitor.headers[1])[:40].ljust(45),
                item.get("status").ljust(9)))


    @staticmethod
    def printServiceStateReport(reportDict):
        for dkey in reportDict:
            serviceList = reportDict.get(dkey)
            for tup in serviceList:
                lst = dkey.split("##")
                print "%s,%s,%s,%s,%s" % (lst[0],lst[1],time.ctime(int(tup[0])),tup[1],tup[2])
    
    @staticmethod
    def writeToFile(reportDict,stime,etime):
        
        f = open("/tmp/ha_infra/nrecord",'w+')
        f.write("starttime##"+stime+"\n")
        for dkey in reportDict:
            serviceList = reportDict.get(dkey)
            for tup in serviceList:
                lst = dkey.split("##")
                print "%s,%s,%s,%s,%s" % (lst[0],lst[1],time.ctime(int(tup[0])),tup[1],tup[2])
                d = datetime.datetime.fromtimestamp(int(tup[0])).strftime('%Y-%m-%d %H:%M:%S')
                f.write("%s,%s,%s,%s,%s\n" % (lst[0],lst[1],d,tup[1],tup[2]))
        f.write("endtime##"+etime+"\n")
        f.close()

    @staticmethod
    def getStatusStr(status):
        if status == '0':
            return "OK"
        elif status == '1':
            return "WARNING" 
        else:
            return "CRITICAL" 

    @staticmethod
    def splitLines(result,ret):
        wordList = result["output"].split( )
        result["output"]=''
        line=''
        status=result["status"]
        for w in wordList:
            if len(line)+len(w) > 40:
                if result["output"] == "":
                    result["output"] = NagiosMonitor.updateStatusColor(status,line)
                    result["status"] = NagiosMonitor.updateStatusColor(status,result["status"])
                    ret.append(result)
                else:
                    res={}
                    res["ip"] = " "
                    res["description"] = " "
                    res["output"] = NagiosMonitor.updateStatusColor(status,line)
                    res["status"] = " "
                    ret.append(res)
                line=w
            else:
                line="%s %s" % (line,w)
        if line != "":
            res={}
            res["ip"] = " "
            res["description"] = " "
            res["output"] = NagiosMonitor.updateStatusColor(status,line)
            res["status"] = " "
            ret.append(res)

    @staticmethod
    def getNagiosData(url, ipaddress):
        try:
            request = urllib2.Request(url % (ipaddress))
            result = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            print "%s" % e.reason()
        json_data = result.read()
        data = json.loads(json_data)
        return data["content"]  # ["services"]

    @staticmethod
    def get_severity_color(severity, text):
        # print severity, text
        if severity == 'CRITICAL':
            return "\033[" + '31' + "m" + text + "\033[0m"
        elif severity == 'WARNING':
            return "\033[" + '33' + "m" + text + "\033[0m".ljust(6)
        elif severity == 'INFO':
            return "\033[" + '32' + "m" + text + "\033[0m"

    @staticmethod
    def do_calc(starttime, endtime, value):
        delta = float((endtime - starttime) / 1000)

        return round((float(value) / delta) * 100, 2)

    def filter_objs(self, objs):
        filter_objs = []
        for obj in objs:
            if obj.get('host_name') in self.ip_filter:
                filter_objs.append(obj)
        return filter_objs

    def get_config(self, key, section='Default'):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.path))

        return config.get(section, key)

    @staticmethod
    def collectFlappingServiceData(ip,desc,reportDict,status,ldesc):
        dkey="%s##%s" % (ip,desc)
        if reportDict.has_key(dkey):
            ipDescStatusList = reportDict.get(dkey)
            listLen = len(ipDescStatusList)
            timeStampStatusTup = ipDescStatusList[listLen - 1]
            if timeStampStatusTup[1] != status:
                tsst=(time.time(),status,ldesc)
        else:
            ipDescStatusList=[]
            tsst=(time.time(),status,ldesc)
            ipDescStatusList.append(tsst)
            reportDict[dkey]=ipDescStatusList

    @staticmethod
    def calSummaryReport(ip,desc,summaryDict,reportDict,status,ldesc):
        dkey="%s##%s" % (ip,desc)
        skey="%s##%s" % (dkey,status)
        if not summaryDict.has_key(skey):
            summaryDict[skey] = 0
        if reportDict.has_key(dkey):
            ipDescStatusList = reportDict.get(dkey)
            listLen = len(ipDescStatusList)
            timeStampStatusTup = ipDescStatusList[listLen - 1]
            if timeStampStatusTup[1] != status:
                pTime = ipDescStatusList[0]
                seconds = time.time().total_seconds() - pTime.total_seconds()
                summaryDict[skey] = summaryDict[skey] + seconds
                print summaryDict[skey]
            
