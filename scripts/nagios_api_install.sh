#!/bin/bash

checkExitStatus(){
        if [ "$1" -ne 0 ]
        then
		echo "================================================="
                echo "$2"
		echo "================================================="
                exit 1
        fi
}
cwd=`pwd`
apt-get install -y python-pip
checkExitStatus $? "Error installing python-pip packages"
apt-get install -y python-dev
checkExitStatus $? "Error installing python-dev packages"
pip install diesel
checkExitStatus $? "Error installing diesel packages"
cd ..
wget https://pypi.python.org/packages/source/n/nagios-api/nagios-api-1.2.2.tar.gz
checkExitStatus $? "Error downloading nagios-api file"
tar xzf nagios-api-1.2.2.tar.gz
if [ ! -d "nagios-api-1.2.2" ]
then
	echo "Nagios API diretory does not exists"
	exit 1
fi
cd nagios-api-1.2.2
nohup python ./nagios-api -p 8080 -c /usr/local/nagios/var/rw/nagios.cmd -s /usr/local/nagios/var/status.dat -l /usr/local/nagios/var/nagios.log &
checkExitStatus $? "Error running the nagios api server"
