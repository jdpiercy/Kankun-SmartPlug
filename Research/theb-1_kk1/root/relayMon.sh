#!/bin/sh

RELAY=/sys/class/leds/tp-link\:blue\:relay/brightness
lastValue=`cat $RELAY`

while true; do
	newValue=`cat $RELAY`
	if [ "$lastValue" != "$newValue" ]; then
		echo "Relay state change: $lastValue > $newValue"
		
		if [ "$newValue" == "1" ]; then
			# Switched On
			
			response=`wget -q -O - http://192.168.1.80/cgi-bin/relay.cgi?on`
			echo "   URL response: $response"
		elif [ "$newValue" == "0" ]; then
			# Switched Off
			
			response=`wget -q -O - http://192.168.1.80/cgi-bin/relay.cgi?off`
			echo "   URL response: $response"
		fi
		
		lastValue=$newValue
	fi
	sleep 1
done
