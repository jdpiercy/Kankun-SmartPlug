#!/bin/sh
# NAME: dasygenis_kankun_control.sh
# URL: http://arch.icte.uowm.gr/mdasyg/misc/dasygenis_kankun_control.sh
# Minas Dasygenis
# http://arch.icte.uowm.gr
#
#

version=006

#Required File Locations
contrlscr="/root/relaycontrol.sh"
watchdog="/root/watchdog.sh"
masterscript="/root/dasygenis_kankun_control.sh"


check_file ()
{
if [ $# -ne 1 ] ; then
	echo "check file function was specified without any argument"
	exit 3
fi

if [ ! -x "$1" ] ; then
	echo "Required File $1 is absent or not executable"
	exit 3
fi
}

	
	
check_file $contrlscr
check_file $watchdog
check_file $masterscript


# The serverIP
server=http://<myIP/smartsocket.php
# The secret
psk=mypassword
# Device iname
name=home


mac=`ifconfig  wlan0 | grep HW | tr -d " " | cut -f 3 -d"r"`
ip=`ifconfig wlan0 | grep "inet " | cut -f 2 -d: | cut -f 1 -d" "`
failcounter=0
restartdone=0
countrun=0
echo "Dasygenis Web Control initiated, scriptversion=$version"
echo "Device with ip $ip and mac $mac and name $name"


#This is a never ending while loop, with 5 sec delay each iteration
while [ 1 -eq 1 ] ;
do
echo -n "."
#ip may change during DHCP, so needs updating...
ip=`ifconfig wlan0 | grep "inet " | cut -f 2 -d: | cut -f 1 -d" "`
status=`$watchdog wget -q ${server}\?psk=${psk}\&ip=${ip}\&mac=${mac}\&name=${name}\&count=${countrun}\&failcounter=${failcounter} -O-`
if [ ! -z "$status" ] ; then
#echo $status
sh $contrlscr $status > /dev/null 2>&1
fi



ping -q -c1 ippower.vlsi.gr > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    failcounter=`expr $failcounter + 1`
	echo -n "F"
else
	#we got an answer, everything is ok
	failcounter=0
	restartdone=0
fi


#ping arch.icte.uowm.gr or bigb6.vlsi.gr and if no answer do a network restart
#network restart, is done only once per failure session
ping -q -c2 62.217.127.198  > /dev/null ||  ping -q -c2 62.217.127.47 > /dev/null
if [ $? -ne 0 -a $failcounter -gt 30 -a $restartdone -eq 0 ];  then
	 echo -n "N"
     /etc/init.d/network reload > /dev/null 2>&1
     /etc/init.d/network restart > /dev/null 2>&1
	 restartdone=1
fi


#at least 5 minutes online (60*5)
if [ "$failcounter" -gt 60 ] ; then
		echo "I Will reboot due to ping error $failcounter"
        reboot 
fi


countrun=`expr $countrun + 1`
sleep 5
done

