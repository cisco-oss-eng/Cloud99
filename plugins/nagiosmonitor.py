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
import ha_engine.ha_infra as infra

# ========================== Configurable Parameters ======================
# Ip address based service filter 
# If IP_FILTER is empty all services will be selected else only ip from IP_FILTER considerd for display

# =========================================================================

class NagiosMonitor(BaseMonitor):

    headers = ['host_name', 'description', 'time_critical',
               'time_ok', 'time_indeterminate_nodata']
    polling_interval = 20
    ip_filter = []
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

        format_string = "%s %s  %s  %s  %s "

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
        run = True
        while(run):
            data = self.getdata(self.url, ip_address)
            ret = []
            for ip in data:
                hostService = data[ip]["services"]
                for key in hostService:
                    result = {}
                    result["ip"] = ip
                    result["description"] = key
                    if data[ip]["services"][key]["current_state"] == '0':
                        result["status"] = "OK"
                        result["output"] = data[ip]["services"][key][
                            "plugin_output"]
                    else:
                        result["status"] = self.get_severity_color("CRITICAL",
                                                                   "CRITICAL")
                        result["output"] = self.get_severity_color(
                            "CRITICAL",
                            data[ip]["services"][key]["plugin_output"])
                    ret.append(result)
            infra.display_on_terminal(self, self.get_severity_color('INFO', format_string % (
                'IP address'.ljust(20), "Service Description".ljust(45),
                "Status".ljust(7), "Status Information", "")))
            infra.display_on_terminal(self, "Polling Interval %s " % (self.polling_interval))
            infra.display_on_terminal(self, "IP Filter : %s " % self.ip_filter)
            for item in ret:
                if self.ip_filter:
                    if item.get("ip") in self.ip_filter:
                        infra.display_on_terminal(self, format_string % (item.get("ip").ljust(20),
                                               item.get(self.headers[1])[:40].ljust(
                                                   45),
                                               item.get("status").ljust(10),
                                               item.get("output"), ""))
                        entries += 1
                else:
                    infra.display_on_terminal(self, format_string % (item.get("ip").ljust(20),
                                           item.get(self.headers[1])[:40].ljust(45),
                                           item.get("status").ljust(7),
                                           item.get("output"), ""))
                    entries += 1

            time.sleep(5)
            '''
            if run_count < 10:
                run_count+=1
                time.sleep(5)
            else:
                run = False
            '''
            #infra.set_execution_completed(finish_execution)
            #time.sleep(20)

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
            return "\033[" + '33' + "m" + text + "\033[0m"
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
    def validate_critical_data(ip, desc, reportList, status):
        # under progress
	if reportList.has_key(ip+desc):
		ipDescStatusList = reportList.get(ip+desc)
		timeStampStatusTup = ipDescStatusList[0]
		if timeStampStatusTup[1] != status:
			tsst=(time.time(),status)
			ipDescStatusList.insert(tsst,0)

	elif status != 'OK':
		ipDescStatusList=[]
		tsst=(time.time(),status)
		ipDescStatusList.insert(tsst,0)
		reportList[ip+desc]=ipDescStatusList
