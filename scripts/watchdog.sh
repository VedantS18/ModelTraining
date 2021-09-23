#!/bin/bash
light_red='\e[1;91m%s\e[0m\n'                     
light_green='\e[1;92m%s\e[0m\n'     
camera_ip_address='191.168.86.6'
locahost_ip_address='191.168.86.1'
ping_url='debian.org'
restart_network=false
restart_service=false
network_status=true

check_network_status()
{
  #Check eh0 and connectivity to IP camera 
  ping -c 2 -q $camera_ip_address > /dev/null             
  if [ "$?" -eq 0 ]; then                          
    printf "$light_green" "[ IP Camera Connected ]"
  else                                              
    printf "$light_red" "[ IP Camera Disconnected ]"
    return 1    
  fi


  #Check wifi network connectivity
  ping -c 2 -q $ping_url > /dev/null
  if [ "$?" -eq 0 ]; then                           
    printf "$light_green" "[ WiFi Connected ]"
  else                                              
    printf "$light_red" "[ WiFi Disconnected ]"     
    return 2
  fi
  return 0
}

reset_ip_network()
{
  #restart network manager if required
  /sbin/ifconfig eth0 $locahost_ip_address netmask 255.255.255.0
}

reset_wifi_network()
{
  systemctl stop NetworkManager
  systemctl restart NetworkManager
  systemctl start networking.service
}

#retry to connect three times
network_reset_happened=false
network_connected=false
for i in 1 2 3 4 5
do
  check_network_status
  network_on=$?
  if [ $network_on == 1 ]; then
    printf "$light_green" "[ Resetting IP Camera... ]"
    reset_ip_network   
  elif [ $network_on == 2 ]; then
    printf "$light_green" "[ Resetting WiFi Network - attempt $i ]"
    reset_wifi_network
    network_reset_happened=true
    #Wait for network to come back online
    sleep 60s

  else
    printf "$light_green" "[ Network Connected ]"
    network_connected=true
    
  fi
done

if [ $network_reset_happened ] && [ network_connected ]; then
  systemctl stop ngrok.service
  systemctl start ngrok.service
fi
