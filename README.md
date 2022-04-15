# ModelTraining
Scripts and Tools necessary for training models


Enter docker
sudo docker run --net=host -it --gpus all -v /home/eqwis/.nv:/root/.nv -v /home/eqwis/.config:/root/.config -v /home/eqwis/Projects/yolov5/:/yolov5 -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix vedantsrinivas/florida:latest

Network maintenance
sudo ifconfig eth0 192.168.1.128 netmask 255.255.255.0
Note the camera default IP address is 192.168.1.13 (sharpshooter) and 192.168.1.64 (govconn)
systemctl disable NetworkManager
systemctl stop NetworkManager
systemctl restart networking.service

