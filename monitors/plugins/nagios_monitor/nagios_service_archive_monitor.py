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

	@staticmethod
	def getdata(url,ipaddress,starttime,endtime):
		try:
			# request = urllib2.Request("http://172.22.191.244/nagios/cgi-bin/archivejson.cgi?query=availability&availabilityobjecttype=services&starttime=1429221978&endtime=1429826778")
			request = urllib2.Request(url%(ipaddress,starttime,endtime))
			base64string = base64.encodestring('%s:%s' % (service_archive_data.get_config('username'),
														  service_archive_data.get_config('password')))
			request.add_header("Authorization", "Basic %s" % base64string)
			result = urllib2.urlopen(request)
		except urllib2.HTTPError as e:
			print e.reason()
		json_data = result.read()
		data = json.loads(json_data)
		return data["data"]#["services"]

	@staticmethod
	def do_calc(starttime,endtime,value):
		delta = float((endtime - starttime)/1000)
		return round((float(value)/delta)*100,2)

	@staticmethod
	def get_config(key,section='Default'):
		config = ConfigParser.ConfigParser()
		path = os.getcwd()+os.sep+'configs'+os.sep+'user_configs'+os.sep+'nagios_config.cfg'
		config.readfp(open(path))
		return config.get(section,key)

	@staticmethod
	def generateData(start_time):
		ip_address = service_archive_data.get_config('nagios_ip')

		# Execution starts here
		entries=0
		data = service_archive_data.getdata(URL,ip_address,-10000,0)
		# Filtering based on ip
		services = data['services']
		selectors = data['selectors']
		ret = []
		for obj in services:
			result = {}
			for header in HEADERS:
				if header in ['time_critical','time_ok','time_indeterminate_nodata']:
					percentage = service_archive_data.do_calc(selectors['starttime'],selectors['endtime'],obj[header])
					result[header] = str(obj[header]) +'('+str(percentage)+'%)'
				else:
					result[header] = obj[header]
				ret.append(result)
		for item in ret:
			# tuncating the description to 30 char for better visibilty ljust()
			print format_string%(item.get(HEADERS[0]),item.get(HEADERS[1])[:40].ljust(40),item.get(HEADERS[3]),item.get(HEADERS[2]),item.get(HEADERS[4]))

if __name__ == '__main__':
	service_archive_data.generateData("");
