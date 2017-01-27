#!/bin/bash
# SUID wrapper enabling gufw application to immediately detect fw status

if  sudo service ufw status; then
    #echo 'yay'
    exit 1
else
    #echo 'nope'
    exit 0
fi
