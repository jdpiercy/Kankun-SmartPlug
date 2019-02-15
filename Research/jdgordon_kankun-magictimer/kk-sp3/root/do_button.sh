#!/bin/sh
#set -ex

ADDR=`cat /sys/devices/platform/ar933x_wmac/net/wlan0/address` 
STATE=`wget -q -O - http://10.0.0.2:8100/api/0.1/$ADDR/button`
POWER=`echo $STATE | sed -r "s/.*power=(\w*).*/\1/"`
TIMER=`echo $STATE | sed -r "s/.*timer=(\w*).*/\1/"`
if [ $POWER = 'ON' ]; then                           
	echo 1 > /sys/class/leds/tp-link\:blue\:relay/brightness
else
	echo 0 > /sys/class/leds/tp-link\:blue\:relay/brightness
fi
if [ $TIMER = 'AUTO' ]; then
	# Blue LED is 1 for off and 0 for on
	echo 0 > /sys/class/leds/tp-link\:blue\:config/brightness
else
	echo 1 > /sys/class/leds/tp-link\:blue\:config/brightness
fi
