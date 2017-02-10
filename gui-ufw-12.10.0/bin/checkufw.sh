#!/bin/bash
# SUID wrapper enabling gufw application to detect and immediately
# display fw status when launched

if  sudo service ufw status; then
    #echo 'yay'
    exit 1
else
    #echo 'nope'
    exit 0
fi
