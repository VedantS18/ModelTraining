#!/bin/bash
light_red='\e[1;91m%s\e[0m\n'                     
light_green='\e[1;92m%s\e[0m\n'     
ip_address='192.168.1.13'
ping_url="www.google.com"
restart_network=false
restart_service=false

check_network_status()
{
  #Check eh0 and connectivity to IP camera              
  ping -c 2 -q $ip_address              
  if [ "$?" -eq 0 ]; then                           
    printf "$light_green" "[ IP Camera Connected ]"
  else                                              
    printf "$light_red" "[ IP Camera Disconnected ]"
    restart_network=true    
  fi


  #Check wifi network connectivity
  ping -c 2 -q $ping_url    
  if [ "$?" -eq 0 ]; then                           
    printf "$light_green" "[ WiFi Connected ]"
  else                                              
    printf "$light_red" "[ WiFi Disconnected ]"     
    restart_network=true
  fi
  if [ $restart_network == true ]; then
    return 1
  fi
  return 0
}

reset_network()
{
  #restart network manager if required
  systemctl stop NetworkManager
  /sbin/ifconfig eth0 192.168.1.1 netmask 255.255.255.0
  systemctl restart NetworkManager
  systemctl start networking.service
}

check_network_status
reset_network_flag=$?
if [ $reset_network_flag == 1 ]; then
  printf "$light_green" "[ Network Reset ]"
  reset_network
  #WAIT FOR A MINUTE
  sleep 30s
else
  printf "$light_green" "[ Network Connected ]"
  exit
fi



check_network_status
reset_network_flag_after=$?

#If the flag went from bad to good, that means most likely eqwis code is corrupted, so restart the eqwis service
if [ $reset_network_flag != $reset_network_flag_after ]; then
  printf "$light_green" "[ Restart Eqwis Service ]"
fi
#Check if eqwis code is running without errors
