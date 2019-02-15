#!/bin/sh

echo 0 > /sys/class/gpio/export

lastValue=`cat /sys/class/gpio/gpio0/value`

while true; do
	newValue=`cat /sys/class/gpio/gpio0/value`
	if [ "$lastValue" != "$newValue" ]; then
		echo State change: $lastValue \> $newValue
		echo $((!`cat /sys/class/leds/tp-link\:blue\:relay/brightness`)) > /sys/class/leds/tp-link\:blue\:relay/brightness
		lastValue=$newValue
	fi
	sleep 1
done
