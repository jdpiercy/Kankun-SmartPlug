#!/bin/sh

BROKER="192.168.1.90"
HOSTNAME=$(uci get system.@system[0].hostname)
TOPIC="home/switch/$HOSTNAME"
RELAY=/sys/class/leds/tp-link\:blue\:relay/brightness
lastValue=`cat $RELAY`

echo "mqtt pub: $BROKER $TOPIC"

while true; do
  newValue=`cat $RELAY`
  if [ "$lastValue" != "$newValue" ]; then
    if [ "$newValue" == "1" ]; then
      # Switched On

      echo "send: $TOPIC = ON"
      mosquitto_pub -h $BROKER -r -t "$TOPIC" -m 'ON'

    elif [ "$newValue" == "0" ]; then
      # Switched Off

      echo "send: $TOPIC = OFF"
      mosquitto_pub -h $BROKER -r -t "$TOPIC" -m 'OFF'
    fi

    lastValue=$newValue
  fi
  sleep 1
done
