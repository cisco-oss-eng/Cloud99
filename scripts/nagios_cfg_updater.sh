#!/bin/bash

if [ -f "nagios_host.cfg" ]
then
	echo "Removing old nagios config file..."
	rm nagios_host.cfg nagios_service.cfg nagios_vm_host.cfg nagios_vm_service.cfg
fi
python monitors/plugins/nagios_monitor/nagios_cfg_generator.py
if [ ! -z "$?"  -a "$?" != 0 ]
then
	echo "Failed tp execute the config generator command"
	exit 2
fi
if [ -f "nagios_host.cfg" ]
then
	cp nagios_host.cfg nagios_service.cfg nagios_vm_host.cfg nagios_vm_service.cfg /usr/local/nagios/etc/servers
	service nagios restart	
fi
if [ ! -z "$?"  -a "$?" != 0 ]
then
	echo "Failed tp execute the config generator command"
	exit 2
else
	echo "Removing newly generated nagios config file "
	rm nagios_host.cfg nagios_service.cfg nagios_vm_host.cfg nagios_vm_service.cfg
fi
 
