#!/bin/bash

export PYTHONUNBUFFERED=1

#exit 0

#cd $HOME || exit 1
current_dir="/home/ubuntu/ardupilot_heartbeat/"

copyit() {
    dst="$1"
    $current_dir/ardupilot_heartbeat_test.py $(cat $HOME/WP_Auth/rover.auth) || {
        #fail
        sudo service apache2 restart
        sudo service varnish restart
	echo $(cat "$current_dir/last_status.html") | mail -s "Heartbeat failed on ardupilot - restarting" hamish@3drobotics.com #andrew-3dr@tridgell.net,
    }
    apache_service_status=$(wget -qO- http://ardupilot.com/server-status)
    echo $apache_service_status > $current_dir/last_status.html
}

(
echo "$(date) starting"
copyit 
echo "$(date) done"
) >> $current_dir/ardupilot_heartbeat.log 2>&1
