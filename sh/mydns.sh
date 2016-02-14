#!/bin/bash
ifconfig | grep ppp > /dev/null
if [ $? == 1 ]; then
wget -q -O /dev/null http://<id>:<pass>@www.mydns.jp/login.html
fi
