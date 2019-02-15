#!/bin/sh

if [ $ACTION = "ifup" ] && [ $DEVICE = "wlan0" ]; then
    rm /etc/hotplug.d/iface/40-setup

    if [[ -e /setup/install.sh ]]; then
        cd /setup
        chmod +x install.sh
        sh install.sh
    fi

    reboot
fi
