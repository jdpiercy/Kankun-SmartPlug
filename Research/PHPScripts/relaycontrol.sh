#!/bin/sh
RELAY_CTRL=/sys/class/leds/tp-link:blue:relay/brightness

if [ $# -ne 1 ] ; then
        echo Usage $0 state/on/off
        exit 3
fi


case "$1" in
        state)
                case "`cat $RELAY_CTRL`" in
                        0) echo "OFF"
                        ;;
                        1) echo "ON"
                        ;;
                esac
        ;;
        on|1)
                echo 1 > $RELAY_CTRL
                echo OK
        ;;
        off|0)
                echo 0 > $RELAY_CTRL
                echo OK
        ;;

	*)
		echo Usage $0 state/on/off
	;;
esac

