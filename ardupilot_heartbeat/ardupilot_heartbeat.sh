#!/bin/bash

export PYTHONUNBUFFERED=1

#exit 0

#cd $HOME || exit 1
current_dir="/home/ubuntu/ardupilot_heartbeat/"
copyit() {
    dst="$1"
#    $current_dir/ardupilot_heartbeat_test.py $(cat forcefail) || {
    $current_dir/ardupilot_heartbeat_test.py $(cat $HOME/WP_Auth/rover.auth) || {
        #fail
        msg_service="COPY EVERYTHING AFTER THIS INTO HTML FILE TO VIEW APACHE SERVICE STATUS:   "
        apache_service_status=$(wget -qO- http://ardupilot.com/server-status)
	echo $msg_service $apache_service_status | mail -s "Heartbeat failed on ardupilot - restarting" hamish@3drobotics.com #andrew-3dr@tridgell.net,
        sudo service apache2 restart
        sudo service varnish restart
    }
}

(
echo "$(date) starting"
copyit 
echo "$(date) done"
) >> $current_dir/ardupilot_heartbeat.log 2>&1
