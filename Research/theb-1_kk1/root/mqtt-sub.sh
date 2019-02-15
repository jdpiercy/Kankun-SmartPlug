#!/bin/sh
BROKER="192.168.1.90"
HOSTNAME=$(uci get system.@system[0].hostname)
TOPIC="home/switch/$HOSTNAME"
RELAY_CTRL="/sys/class/leds/tp-link:blue:relay/brightness"

echo "mqtt sub: $BROKER $TOPIC"

while :
do
  mosquitto_sub -h "$BROKER" -t "$TOPIC" | while read line
  do
    #line=`echo $line | tr [A-Z] [a-z]`
    echo "received: $TOPIC = $line"
    case "$line" in
      on|ON)
        echo 1 > $RELAY_CTRL
      ;;
      off|OFF)
        echo 0 > $RELAY_CTRL
      ;;
      toggle|TOGGLE)
        echo $((!`cat $RELAY_CTRL`)) > $RELAY_CTRL
      ;;
   esac
  done
  
  sleep 1
done
