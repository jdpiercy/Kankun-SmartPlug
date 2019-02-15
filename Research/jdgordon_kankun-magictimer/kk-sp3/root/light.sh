#!/bin/sh
#set -ex



TIMEFILE="/tmp/suntimes.xml"
LAT_LONG="-37.8/144.96"
TZ="10/0"

get_xml_tag () {
	TAG=$1
	REGEX="<$TAG>\(.*\)<\/$TAG>"
	grep $TAG $TIMEFILE | sed -e "s/$REGEX/\1/"
}

update_timefile () {
	wget -q -O $TIMEFILE http://www.earthtools.org/sun/$LAT_LONG/`date +%d/%m`/$TZ
	return $?
}

check_timefile () {
	if [ -f $TIMEFILE ]; then
		DAY=$(get_xml_tag day)
		MONTH=$(get_xml_tag month)
		if [ $DAY = `date +%d` -a $MONTH = `date +%m` ]; then
			return 1
		fi
	fi
	
	return 0
}

turn_power_on () {
	SUNRISE=$(get_xml_tag sunrise)
	SUNRISE_H=`echo $SUNRISE | cut -d: -f1`
	SUNRISE_M=`echo $SUNRISE | cut -d: -f2`
	SUNSET=$(get_xml_tag sunset)
	SUNSET_H=`echo $SUNSET | cut -d: -f1`
	SUNSET_M=`echo $SUNSET | cut -d: -f2`
	NOW=`date +%k%M`
	DAY=`date +%a`

#	off_time="2130"
#	on_time=$((SUNSET_H-2))$SUNSET_M


	#turn off 1hr after sunrise
	off_time=$((SUNRISE_H+1))$SUNRISE_M
	
	# turn on 1hr before sunset
	on_time=$((SUNSET_H-1))$SUNSET_M

	if [ $on_time -lt $off_time ]; then
		OP="-a"
	else
		OP="-o"
	fi

	echo "$on_time -lt $NOW $OP $NOW -lt $off_time" >> /tmp/light.log
	# Turn the power on 1hr before sunset and off 1hr
	if [ $on_time -lt $NOW $OP $NOW -lt $off_time  ]; then
		return 0
	else
		return 1
	fi
}

while true; do
	ADDR=`cat /sys/devices/platform/ar933x_wmac/net/wlan0/address` 
	STATE=`wget -q -O - http://10.0.0.2:8100/api/0.1/$ADDR`
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
	sleep 30	
done

echo $?
