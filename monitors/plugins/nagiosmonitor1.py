# Service monitor - updates the service status every configured interval
# Service configruations refer 

from pprint import pprint
import urllib2
import json
import base64
import time
import ConfigParser
import os
import sys
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

        format_string = "%s  |  %s  |  %s  |  %s  |  %s  | "
        input = self.get_input_arguments()
        i = 0
        inputs = sys.argv[1:]
        for arg in inputs:
            if arg == 'ip':
                IP_FILTER = inputs[i + 1].split(',')
            elif arg == 'fre':
                POLLING_INTERVAL = float(inputs[i + 1])
            i = i + 1

        ip_address = self.get_config('nagios_ip')

        # Execution starts here
        entries = 0
        while(finish_execution):
            data = self.getdata(self.url, ip_address)
            ret = []
            for ip in data:
                hostService = data[ip]["services"]
                for key in hostService:
                    result = {}
                    result["ip"] = ip
                    result["description"] = key
		    status_str = self.getStatusStr(
                data[ip]["services"][key]["current_state"])
		    result["status"] = status_str
		    result["output"] = data[ip]["services"][key]["plugin_output"]

		    if len(result["output"]) < 40:
		        ret.append(result)
		    else:
		        self.splitLines(result,ret)

		    self.collectFlappingServiceData(ip,key,self.reportDict,result["status"],data[ip]["services"][key]["plugin_output"])
	    print '-' * 160
            print self.get_severity_color('INFO', format_string % (
		'TimeStamp'.ljust(25),'HostName'.ljust(20),
		"Service Description".ljust(45),
                "Status".ljust(9), "Status Information".ljust(40)))
	    print '-' * 160
            #print "Polling Interval %s " % (self.polling_interval)
            #print "IP Filter : %s " % self.ip_filter
            for item in ret:
                # tuncating the description to 30 char for better visibilty ljust()
                if self.ip_filter != []:
                    if item.get("ip") in self.ip_filter:
			self.printData(format_string,item)
                        #print format_string % (time.ctime(int(time.time())).ljust(25),
			#			item.get("ip").ljust(20),
                        #                       item.get(self.headers[1])[:40].ljust(45),
                        #                       item.get("status").ljust(9),
                        #                       item.get("output").ljust(40))
                        entries = entries + 1
                else:
		    self.printData(format_string,item)
                    #print format_string % (time.ctime(int(time.time())).ljust(25),
		#			   item.get("ip").ljust(20),
                #                           item.get(self.headers[1])[:40].ljust(45),
                #                           item.get("status").ljust(9),
                #                           item.get("output").ljust(40))
                    entries = entries + 1
	    print '-' * 160

	    for dkey in self.reportDict:
	        serviceList = self.reportDict.get(dkey)
	    	for tup in serviceList:
		    lst = dkey.split("##")
		    print "%s,%s,%s,%s,%s" % (lst[0],lst[1],time.ctime(int(tup[0])),tup[1],tup[2])
            time.sleep(20)


    @staticmethod
    def updateStatusColor(status,statusDesc):
        if status == "OK":
            return statusDesc
        elif status == "WARNING":
            return NagiosMonitor.get_severity_color("WARNING",
							statusDesc)
        else:
            return NagiosMonitor.get_severity_color("CRITICAL",
							statusDesc)

    @staticmethod
    def printData(format_string,item):
        print format_string % (time.ctime(int(time.time())).ljust(25),
				item.get("ip").ljust(20),
                                item.get(NagiosMonitor.headers[1])[:40].ljust(45),
                                item.get("status").ljust(9),
                                item.get("output").ljust(40))

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
    def getdata(url, ipaddress):
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
		timeStampStatusTup = ipDescStatusList[0]
		if timeStampStatusTup[1] != status:
			tsst=(time.time(),status,ldesc)
			ipDescStatusList.insert(0,tsst)
	elif status != 'OK':
		ipDescStatusList=[]
		tsst=(time.time(),status,ldesc)
		ipDescStatusList.insert(0,tsst)
		reportDict[dkey]=ipDescStatusList
