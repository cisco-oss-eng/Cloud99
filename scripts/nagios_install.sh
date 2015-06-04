#!/bin/bash
TMP_NAGIOS_INSTALL_DIR=/tmp/nagios_install

checkExitStatus(){
	if [ "$1" -ne 0 ]
	then
		echo "$2"
		exit 1
	fi
}


echo "====================================="
echo "Installing Nagios Monitoring Packages"
echo "====================================="
echo ""
nstatus=`sudo service nagios status | grep running`
if [ $? -eq 0 ]
then
	echo "Nagios Service is running - stopping the service"
	sudo service nagios stop
fi
echo "Do you want to run \"apt-get update\" before installing nagios packages(y/n)? "
read response
if [ ! -z "$response" -a "$response" = 'y' ]
then
	echo "Updating the system "
	apt-get -y update 
fi
echo ""
echo "Installing nagios pre-requiste - build-essential libgd2-xpm-dev apache2-utils"
apt-get install -y php5 libapache2-mod-php5
apt-get install -y apache2
apt-get install -y build-essential libgd2-xpm-dev apache2-utils
checkExitStatus $? "Error in installing pre-requiste"
naguser=`cut -d: -f1 /etc/passwd | grep nagios`
if [ ! -z "$naguser" -a "$naguser" = 'nagios' ]
then 
	echo "User nagios exists - assuming nagcmd group also exists"
else
	useradd -m nagios
	groupadd nagcmd
	usermod -a -G nagcmd nagios
	usermod -a -G nagcmd www-data
fi

echo "nagios:nagios"| sudo chpasswd

echo ""
echo "Downloading nagios system file"
echo ""
if [ -d $TMP_NAGIOS_INSTALL_DIR ]
then
	rm -rf $TMP_NAGIOS_INSTALL_DIR
fi
mkdir $TMP_NAGIOS_INSTALL_DIR
cd $TMP_NAGIOS_INSTALL_DIR
if [ -f "nagios-4.0.8.tar.gz" ]
then
	echo "File exists - nagios-4.0.8.tar.gz"
else
	wget http://prdownloads.sourceforge.net/sourceforge/nagios/nagios-4.0.8.tar.gz
fi
echo ""
checkExitStatus $? "Error downloading the nagios system - http://prdownloads.sourceforge.net/sourceforge/nagios/nagios-4.0.8.tar.gz"

echo ""
echo "Downloading nagios plugin file"
echo ""
if [ -f "nagios-plugins-2.0.3.tar.gz" ]
then
        echo "File exists - nagios-plugins-2.0.3.tar.gz"
else
	wget http://nagios-plugins.org/download/nagios-plugins-2.0.3.tar.gz
fi
echo ""
checkExitStatus $? "Error downloading the nagios plugin - http://nagios-plugins.org/download/nagios-plugins-2.0.3.tar.gz"

tar xzf nagios-4.0.8.tar.gz
checkExitStatus $? "Error extracting the file nagios-4.0.8.tar.gz"
if [ -d "nagios-4.0.8" ]
then
	echo "Changing the directory to nagios-4.0.8"
	cd nagios-4.0.8
else
	echo "Nagios core system installation files does not exists"
	exit 1
fi
./configure --with-command-group=nagcmd
make all
make install
make install-init
make install-config
make install-commandmode
make install-webconf
/usr/bin/install -c -m 644 sample-config/httpd.conf /etc/apache2/sites-enabled/nagios.conf
echo "Enter Nagios WebInterface password for the user nagiosadmin "
htpasswd -c /usr/local/nagios/etc/htpasswd.users nagiosadmin
service apache2 restart
cd ..

tar xzf nagios-plugins-2.0.3.tar.gz
checkExitStatus $? "Error extracting the file nagios-plugins-2.0.3.tar.gz"
if [ -d "nagios-plugins-2.0.3" ]
then
        echo "Changing the directory to nagios-4.0.8"
	cd nagios-plugins-2.0.3
else
        echo "Nagios plugins file does not exists"
        exit 1
fi

./configure --with-nagios-user=nagios --with-nagios-group=nagios
make
make install
a2enmod rewrite
a2enmod cgi
service apache2 restart
lsout=`ls -al /etc/rcS.d/S99nagios`
if [ $? -ne 0 ]
then
	ln -s /etc/init.d/nagios /etc/rcS.d/S99nagios
fi
cd ..
service nagios start
echo "Removing temporary files"
rm -rf $TMP_NAGIOS_INSTALL_DIR
echo "Nagios installation completed successfully"
