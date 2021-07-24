export WORKON_HOME=/home/vedant/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
workon opencv_cuda
cd /home/vedant/test/YOLO3-4-Py
espeak "Waiting for 30 seconds before starting"
sleep 3
espeak "Starting Ora now"
python3 ora_demo.py


