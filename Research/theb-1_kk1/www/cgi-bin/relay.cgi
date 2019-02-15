#!/bin/sh
echo "Content-Type: text/plain"
echo "Cache-Control: no-cache, must-revalidate"
echo "Expires: Sat, 26 Jul 1997 05:00:00 GMT"
echo

RELAY_CTRL=/sys/class/leds/tp-link:blue:relay/brightness

case "$QUERY_STRING" in
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

[ -z "$QUERY_STRING_POST" \
  -a "$REQUEST_METHOD" = "POST" -a ! -z "$CONTENT_LENGTH" ] && \
	read -n $CONTENT_LENGTH QUERY_STRING_POST

case "$QUERY_STRING_POST" in
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

case "`cat $RELAY_CTRL`" in
    0) echo -n "OFF"
    ;;
    1) echo -n "ON"
    ;;
esac


#Example HomeAssistant config:
#
#switch:
#  name: "Bedroom Light"
#  platform: rest
#  resource: http://192.168.1.80/cgi-bin/relay.cgi