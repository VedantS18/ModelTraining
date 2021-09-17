#!/bin/sh

/opt/ngrok/ngrok start --all --config /opt/ngrok/ngrok.yml --log=stdout >> /home/vedant/logs/ngrok.log &
