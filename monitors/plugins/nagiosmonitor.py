import urllib2
import json
import time
import datetime
import ConfigParser
import os
import ha_engine.ha_infra as infra
from monitors.baseMonitor import BaseMonitor


class NagiosMonitor(BaseMonitor):

    headers = ['host_name', 'description', 'time_critical',
               'time_ok', 'time_indeterminate_nodata']
    polling_interval = 20
    ip_filter = []
    reportDict = {}
    summaryDict = {}
    url = "http://%s:8080/state"
    path = os.getcwd() + os.sep + 'configs/user_configs/nagios_config.cfg'
    finish_execution = None

    def stop(self):
        pass

    def report(self):
        pass

    def stable(self):
        pass

    def is_module_exeution_completed(self, finish_exection):
        pass

    def start(self, sync=None, finish_execution=None):

        self.finish_execution = finish_execution
        ip_address = self.get_config('nagios_ip')
        input_args = self.get_input_arguments()
        filter_type = str(input_args['nagios']['type'])

        host_config = infra.get_openstack_config()
        host_filter = []
        if filter_type == "node":
            host_filter = self.generate_filter_list(host_config,filter_type)

        # Execution starts here
        if sync:
            infra.display_on_terminal(self, "Waiting for Runner Notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification from Runner")

        start_time = datetime.datetime.\
            fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        
        while infra.is_execution_completed(self.finish_execution) is False:
            data = self.get_nagios_data(self.url, ip_address)
            self.process_and_report(data, self.reportDict, host_filter,
                                    filter_type)
            time.sleep(20)

        end_time = datetime.\
            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        end_seconds = time.time()

        NagiosMonitor.write_to_file(self.reportDict, start_time, end_time)
        NagiosMonitor.calSummaryReport(self.summaryDict,
                                       self.reportDict, end_seconds)

        self.health_display_report()

    def process_and_report(self, data, report_dict, host_filter, filter_type):
        format_string = "%s  |  %s  |  %s  | "
        ret = []
        for ip in data:
            host_services = data[ip]["services"]
            for key in host_services:
                result = {}
                if host_filter:
                    if ip in host_filter:
                        result = self.create_result_dict(data,ip,key)
                elif filter_type == "openstackvm":
                    if ip.startswith("AppVm-"):
                        result = self.create_result_dict(data,ip,key)
                else:
                    result = self.create_result_dict(data,ip,key)

                if len(result) <= 0:
                    continue
                
                result['status'] = \
                    NagiosMonitor.update_status_color(result['status'],
                                                    result["status"])
                ret.append(result)

                NagiosMonitor.collect_flapping_service_data(ip,
                                                         key,
                                                         report_dict,
                                                         NagiosMonitor.
                                                         get_status_string(
                                                             data[ip]
                                                             ["services"][key]
                                                             ["current_state"]),
                                                         data[ip]["services"]
                                                         [key]["plugin_output"])
        
        tbl_line = '-' * 62
        infra.display_on_terminal(self, tbl_line)

        infra.display_on_terminal(self, NagiosMonitor.get_severity_color(
            'INFO', format_string % (
                'HostName'.ljust(15),
                "Service Description".ljust(25),
                "Status".ljust(9))))
        infra.display_on_terminal(self, tbl_line)
        
        for item in ret:
            if item.get("ip") == " " and item.get("description") == " ":
                self.print_data(format_string,item)
                continue
            if host_filter:
                if item.get("ip") in host_filter: 
                    self.print_data(format_string, item)
            elif filter_type == "openstackvm":
                if item.get("ip").startswith("AppVm-"):
                    self.print_data(format_string, item)
            else:
                self.print_data(format_string, item)
                
        infra.display_on_terminal(self, tbl_line)


    @staticmethod
    def generate_filter_list(host_config, filter_type):
        filter_list = []
        if filter_type == 'node':
            for key in host_config.keys():
                if host_config[key]["role"] == "controller" or \
                        host_config[key]["role"] == "network" or \
                        host_config[key]["role"] == "compute":
                    filter_list.append(key)

        return filter_list
    
    @staticmethod
    def create_result_dict(data, ip, key):
        result = {}
        result["ip"] = ip  # key should be changed into host
        result["description"] = key
        status_str = NagiosMonitor.\
            get_status_string(data[ip]["services"][key]["current_state"])
        result["status"] = status_str
        result["output"] = data[ip]["services"][key]["plugin_output"]
        return result

    @staticmethod
    def update_status_color(status, status_desc):
        if status == "OK":
            return status_desc
        else:
            return NagiosMonitor.get_severity_color("CRITICAL", status_desc)

    def print_data(self, format_string, item):
        infra.display_on_terminal(self, format_string % (
                item.get("ip").ljust(15),
                item.get(NagiosMonitor.headers[1])[:40].ljust(25),
                item.get("status").ljust(9)))


    @staticmethod
    def print_service_state_report(report_dict):
        for dkey in report_dict:
            _l = report_dict.get(dkey)
            for tup in _l:
                lst = dkey.split("##")
                print "%s,%s,%s,%s,%s" % (lst[0], lst[1],
                                          time.ctime(int(tup[0])),
                                          tup[1], tup[2])
    
    @staticmethod
    def write_to_file(report_dict, stime, etime):
        
        with open("/tmp/ha_infra/nrecord",'w+') as f:
            f.write("starttime##"+stime+"\n")
            for dkey in report_dict:
                serviceList = report_dict.get(dkey)
                for tup in serviceList:
                    lst = dkey.split("##")
                    d = datetime.datetime.\
                        fromtimestamp(int(tup[0])).strftime('%Y-%m-%d %H:%M:%S')
                    f.write("%s,%s,%s,%s,%s\n" % (lst[0], lst[1],
                                                  d, tup[1], tup[2]))
            f.write("endtime##"+etime+"\n")

    @staticmethod
    def get_status_string(status):
        if status == '0':
            return "OK"
        elif status == '1':
            return "CRITICAL" 
        else:
            return "CRITICAL" 

    @staticmethod
    def split_lines(result, ret):
        word_list = result["output"].split( )
        result["output"] = ''
        line=''
        status=result["status"]
        for w in word_list:
            if len(line)+len(w) > 40:
                if result["output"] == "":
                    result["output"] = NagiosMonitor.update_status_color(
                        status, line)
                    result["status"] = NagiosMonitor.update_status_color(
                        status, result["status"])
                    ret.append(result)
                else:
                    res={}
                    res["ip"] = " "
                    res["description"] = " "
                    res["output"] = NagiosMonitor.update_status_color(status,
                                                                      line)
                    res["status"] = " "
                    ret.append(res)
                line=w
            else:
                line="%s %s" % (line,w)
        if line != "":
            res={}
            res["ip"] = " "
            res["description"] = " "
            res["output"] = NagiosMonitor.update_status_color(status, line)
            res["status"] = " "
            ret.append(res)

    @staticmethod
    def get_nagios_data(url, ipaddress):
        try:
            request = urllib2.Request(url % ipaddress)
            result = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            print "%s" % e.reason()
        json_data = result.read()
        data = json.loads(json_data)
        return data["content"]  # ["services"]

    @staticmethod
    def get_severity_color(severity, text):
        if severity == 'CRITICAL':
            return "\033[" + '31' + "m" + text + "\033[0m".ljust(5)
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
    def collect_flapping_service_data(ip, desc, reportDict, status, ldesc):
        dkey="%s##%s" % (ip,desc)
        if reportDict.has_key(dkey):
            ipDescStatusList = reportDict.get(dkey)
            listLen = len(ipDescStatusList)
            timeStampStatusTup = ipDescStatusList[listLen - 1]
            if timeStampStatusTup[1] != status:
                tsst=(time.time(),status,ldesc)
                ipDescStatusList.append(tsst)
        else:
            ipDescStatusList=[]
            tsst=(time.time(),status,ldesc)
            ipDescStatusList.append(tsst)
            reportDict[dkey]=ipDescStatusList

    @staticmethod
    def calSummaryReport(summaryDict,reportDict,endSeconds):
        for dkey in reportDict:
            serviceList = reportDict.get(dkey)
            prevTup = ()
            for tup in serviceList:
                skey="%s##%s" % (dkey,tup[1])
                if not summaryDict.has_key(skey):
                    summaryDict[skey] = 0
                
                if len(prevTup) > 0:
                    pkey="%s##%s" % (dkey,prevTup[1])
                    ptime = summaryDict[pkey] 
                    seconds = tup[0] - prevTup[0]
                    summaryDict[pkey] = ptime + seconds
                    
                prevTup = tup
                
            pkey="%s##%s" % (dkey,prevTup[1])
            ptime = summaryDict[pkey] 
            seconds = endSeconds - prevTup[0]
            summaryDict[pkey] = ptime + seconds

    def health_display_report(self):
        infra.create_report_table(self, "Nagios Montitor Summary Repory")
        infra.add_table_headers(self, "Nagios Montitor Summary Repory",
                                ["Host", "Description", "OK(secs)",
                                 "CRITICAL(secs)"])
        processedKey = {}
        for key in self.summaryDict:
            if processedKey.has_key(key):
                continue
            lst = key.split("##")
            key2 = ""
            ok_sec = 0
            crit_sec = 0
            if lst[2] == "OK":
                key2 = lst[0]+"##"+lst[1]+"##CRITICAL"
                ok_sec = int(self.summaryDict[key])
            else:
                key2 = lst[0]+"##"+lst[1]+"##OK"
                crit_sec = int(self.summaryDict[key])
                
            if  self.summaryDict.has_key(key2):
                processedKey[key2] = key2
                if ok_sec > 0:
                    crit_sec = int(self.summaryDict[key2])
                else:
                    ok_sec = int(self.summaryDict[key2])
            
            infra.add_table_rows(self, "Nagios Montitor Summary Repory",
                                 [[lst[0], lst[1],ok_sec,crit_sec]])
            
