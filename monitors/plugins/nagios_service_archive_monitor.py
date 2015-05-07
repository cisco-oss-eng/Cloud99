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

# ========================== Configurable Parameters ======================
# Ip address based service filter 
# If IP_FILTER is empty all services will be selected else only ip from IP_FILTER considerd for display
IP_FILTER = []

# The list of fields needs to be displayed
HEADERS = ['host_name','description','time_critical','time_ok','time_indeterminate_nodata']

# Polling interval - In seconds
POLLING_INTERVAL = 20

URL = "http://%s/nagios/cgi-bin/archivejson.cgi?query=availability&availabilityobjecttype=services&starttime=%s&endtime=%s"
# =========================================================================


class service_archive_data(object):

	def getdata(url,ipaddress,starttime,endtime):
		try:
			# request = urllib2.Request("http://172.22.191.244/nagios/cgi-bin/archivejson.cgi?query=availability&availabilityobjecttype=services&starttime=1429221978&endtime=1429826778")
			request = urllib2.Request(url%(ipaddress,starttime,endtime))
			base64string = base64.encodestring('%s:%s' % (get_config('username'), get_config('password')))
			request.add_header("Authorization", "Basic %s" % base64string)
			result = urllib2.urlopen(request)
		except urllib2.HTTPError as e:
			print e.reason()
		json_data = result.read()
		data = json.loads(json_data)
		return data["data"]#["services"]

	def get_severity_color(severity,text):
		# print severity, text
		if severity == 'CRITICAL':
			return "\033[" + '31' + "m" + text + "\033[0m"
		elif severity == 'WARNING':
			return "\033[" + '33' + "m" + text + "\033[0m"
		elif severity == 'INFO':
			return "\033[" + '32' + "m" + text + "\033[0m"



	def do_calc(starttime,endtime,value):
		delta = float((endtime - starttime)/1000)
		return round((float(value)/delta)*100,2)

	def filter_objs(objs):
		filter_objs = []
		for obj in objs:
			if obj.get('host_name') in IP_FILTER:
				filter_objs.append(obj)
		return filter_objs

	def get_config(key,section='Default'):
		config = ConfigParser.ConfigParser()
		path = os.getcwd()+os.sep+'nagios_config.cfg'
		config.readfp(open(path))
		return config.get(section,key)


# =================== main ================
if __name__ == '__main__':
	format_string = "%s \t %s \t\t\t %s \t %s \t %s "
	print get_severity_color('INFO',format_string%('IP address',"Description".ljust(40),"Time ok","Time critical","Time indeterminate nodata"))

	i=0   
	args = []
	starttime = ''
	endtime = ''
	inputs = sys.argv[1:]
	for arg in inputs:
		if arg  == 'ip':
			IP_FILTER  = inputs[i+1].split(',')
		elif arg == 'int':
			args = inputs[i+1].split(',')
		elif arg == 'fre':
			POLLING_INTERVAL = float(inputs[i+1])
		i=i+1
	if args != []:
		starttime = args[0]
		endtime = args[1]
	else:
		starttime = get_config('start_time')
		endtime = get_config('end_time')
	print "Start time : %s, End Time : %s , Polling Interval %s " % (starttime,endtime,POLLING_INTERVAL)
	print "IP Filter : %s " % IP_FILTER
	ip_address = get_config('nagios_ip')

	# Execution starts here
	entries=0
	while(True):
		data = getdata(URL,ip_address,starttime,endtime)
		# Filtering based on ip
		if IP_FILTER == []:
			services = data['services']
		else:
			services = filter_objs(data['services'])
			# print services
		selectors = data['selectors']
		ret = []
		for obj in services:
			result = {}
			for header in HEADERS:
				if header in ['time_critical','time_ok','time_indeterminate_nodata']:
					percentage = do_calc(selectors['starttime'],selectors['endtime'],obj[header])
					# setting severity to critical time
					if header == 'time_critical' and percentage > 0:
						result[header] = get_severity_color('CRITICAL',str(obj[header]) +'('+str(percentage)+'%)')
					else:
						result[header] = str(obj[header]) +'('+str(percentage)+'%)'
				else:
					result[header] = obj[header]
			ret.append(result)
		for item in ret:
			# tuncating the description to 30 char for better visibilty ljust()
			print format_string%(item.get(HEADERS[0]),item.get(HEADERS[1])[:40].ljust(40),item.get(HEADERS[3]),item.get(HEADERS[2]),item.get(HEADERS[4]))
			entries=entries+1
			if entries >= 20:
				print get_severity_color('INFO',format_string%('IP address',"Description".ljust(40),"Time ok","Time critical","Time indeterminate nodata"))
				entries=0

		time.sleep(POLLING_INTERVAL)
