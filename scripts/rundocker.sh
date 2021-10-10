/usr/bin/docker run -it --net=host --gpus all -v /home/vedant/.nv:/root/.nv -v /home/vedant/projects/docker_yolov5/:/yolov5 -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix vedantsrinivas/eqwis:jetson_nano python3 yolov5/standard/eqwis.py



ExecStart=/home/vedant/projects/eqwis-tools/scripts/rundocker.sh > /home/vedant/logs/eqwis.logs