#Check if there is enough power
myLevel=$(cat "/sys/class/power_supply/BAT1/capacity")
echo ${myLevel}
if on_ac_power; then
   echo "You are on AC-Power" # System is on mains power
   if [ $myLevel -le 99 ] ; then 
      echo "Charging"
   fi
 else
   echo "Power Lost - Checking Battery"          # System is not on mains power
   #shutdown and wake up in some time to check again
   if [ $myLevel -le 99 ] ; then 
      echo "Critical Batttery - Shutting Down"
      sudo rtcwake -u -s 3600 -m off
   fi
fi
