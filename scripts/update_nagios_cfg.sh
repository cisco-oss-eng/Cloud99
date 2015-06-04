#!/bin/bash

cfgFile=/usr/local/nagios/etc/nagios.cfg
cwd=`pwd`
checkExitStatus(){
        if [ "$1" -ne 0 ]
        then
                echo "$2"
                exit 1
        fi
}

updateNagiosCfgFile(){
	if [ -f "$TMP_NAGIOS_INSTALL_CONFIG_DIR/$1" ]
	then
		gResult=`grep $1 $cfgFile`
		if [ $? -eq 1 ]
		then
			echo "cfg_file=/usr/local/nagios/etc/servers/$1" >> "$TMP_NAGIOS_INSTALL_CONFIG_DIR/nagios_new.cfg"
		fi
	fi
}

copyNagiosCfg(){
	if [ -f "$TMP_NAGIOS_INSTALL_CONFIG_DIR/$1" ]
        then
		cp "$TMP_NAGIOS_INSTALL_CONFIG_DIR/$1" $2
	fi

}

if [ ! -f "$cfgFile" ]
then
        echo "Nagios config file does not exists - could be because of nagios installation error"
        exit 1
fi
flag='f'
TMP_NAGIOS_INSTALL_DIR=/tmp/nagios_install
TMP_NAGIOS_INSTALL_CONFIG_DIR=/tmp/nagios_install/config
if [ ! -d $TMP_NAGIOS_INSTALL_DIR ]
then
	mkdir $TMP_NAGIOS_INSTALL_DIR
fi
cd $TMP_NAGIOS_INSTALL_DIR
if [ ! -d $TMP_NAGIOS_INSTALL_CONFIG_DIR ]
then
	mkdir $TMP_NAGIOS_INSTALL_CONFIG_DIR
else
	cd $TMP_NAGIOS_INSTALL_CONFIG_DIR
	echo "Removing old config file"
	sudo rm *
fi
cd $cwd
source install.sh
python monitors/plugins/nagios_monitor/nagios_cfg_generator.py $1
checkExitStatus $? "Error generating nagios config"
cp scripts/nagios_command.cfg $TMP_NAGIOS_INSTALL_CONFIG_DIR 
cp /usr/local/nagios/etc/nagios.cfg $TMP_NAGIOS_INSTALL_CONFIG_DIR/nagios_new.cfg


#while read -r line
#do
#	if [ ! -z "$line" ]
#	then
#		echo $line
#		if [[ "$line" == *cfg_file* ]]
#		then
#			if [[ "$line" == *localhost.cfg* ]]
#			then
#				flag='t'
#			fi
#		fi
#	fi
#	echo $flag
#	if [ $flag = 't' ]
#	then 
#		echo "Adding new config file entries"
#		updateNagiosCfgFile nagios_host.cfg
#		updateNagiosCfgFile nagios_service.cfg
#		updateNagiosCfgFile nagios_vm_host.cfg
#		updateNagiosCfgFile nagios_vm_service.cfg
#		updateNagiosCfgFile nagios_command.cfg
#		flag='f'
#	else
#		echo "$line" >> "$TMP_NAGIOS_INSTALL_CONFIG_DIR/nagios_new.cfg"
#	fi
#done < "$cfgFile"

echo "Adding new config file entries"
updateNagiosCfgFile nagios_host.cfg
updateNagiosCfgFile nagios_service.cfg
updateNagiosCfgFile nagios_vm_host.cfg
updateNagiosCfgFile nagios_vm_service.cfg
updateNagiosCfgFile nagios_command.cfg

nagiosServer=/usr/local/nagios/etc/servers
if [ ! -d $nagiosServer ]
then
	mkdir $nagiosServer
fi
copyNagiosCfg nagios_host.cfg $nagiosServer
copyNagiosCfg nagios_service.cfg $nagiosServer
copyNagiosCfg nagios_vm_host.cfg $nagiosServer
copyNagiosCfg nagios_vm_service.cfg $nagiosServer
copyNagiosCfg nagios_command.cfg $nagiosServer
copyNagiosCfg nagios_new.cfg /usr/local/nagios/etc/nagios.cfg

sudo service nagios restart
