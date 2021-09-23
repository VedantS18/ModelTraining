import time
from datetime import datetime
import pydarknet
from pydarknet import Detector, Image
import cv2
import csv
import os

#the neural network configuration
config_path = "cfg/yolov3.cfg"

#the YOLO net weights file
weights_path = "weights/yolov3.weights"

#metadata file
csvFilepath = "./output/metadata.csv"

#loading all the class labels (objects)
labels = open("data/coco.names").read().strip().split("\n")

#output folder for raw and processed images
output_path = "./output/"

#categories to look for
categories = ["sheep", "horse", "cow", "person"]

#how often to register a detection in seconds
detectionTimeThresholdInSeconds = 5

#file variables
writer = None
file = None

lastDetectionTime = None

def csvOpenFile() :
    global writer
    global file
    #create the required directory structure
    if (os.path.isdir(output_path) == False):
        os.mkdir(output_path)
    if(os.path.isfile(csvFilepath) == True):
        with open(csvFilepath, 'a', newline = '') as file:
            writer = csv.writer(file)
    else:
        with open(csvFilepath, 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "OriginalImagePath", "AnnotatedImagePath", "Confidence"])


#Register metadata into csv with format "Date", "Time", "OriginalImagePath", "AnnotatedImagePath", "Confidence"
def csvUpdateFile(_originalImagePath, _annotatedImagePath, _confidence, category):
    global writer
    global file
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    if(cat in categories):     
        if(os.path.isfile(csvFilepath) == True):
            with open(csvFilepath, 'a', newline = '') as file:
                writer = csv.writer(file)
                writer.writerow([dt_string, _originalImagePath, _annotatedImagePath, _confidence, category])
        else:
            with open(csvFilepath, 'w', newline = '') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "OriginalImagePath", "AnnotatedImagePath", "Confidence", "Category"])
                writer.writerow([dt_string, _originalImagePath, _annotatedImagePath, _confidence])
        

def checkClassesFound(_results) :
    foundCategory = False
    for cat, score, bounds in _results:
        if (cat in categories) :
            return True
    return False


def detectionWindowPass() :
    global lastDetectionTime
    if (lastDetectionTime == None) :
        lastDetectionTime = time.time()

    currentDetectionTime = time.time()
    if (currentDetectionTime - lastDetectionTime > detectionTimeThresholdInSeconds) :
        lastDetectionTime = currentDetectionTime
        return True
    return False

if __name__ == "__main__":
    csvOpenFile()
    lastDetectionTime = time.time()
    # Optional statement to configure preferred GPU. Available only in GPU version.
    # pydarknet.set_cuda_device(0)

    net = Detector(bytes("cfg/yolov3.cfg", encoding="utf-8"), bytes("weights/yolov3.weights", encoding="utf-8"), 0,
                   bytes("cfg/coco.data", encoding="utf-8"))

    #cap = cv2.VideoCapture('rtsp://admin:M*ttapalli8*@191.168.86.6:554/unicast/c1/s0/live')
    cap = cv2.VideoCapture(0)
    #cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) # depends on fourcc available camera
    #cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    #cap.set(cv2.CAP_PROP_FPS, 15)

    while True:
        #check for detection of horses and set the flag save the metadata
        foundClasses = False;
        r, frame = cap.read()
        #original_frame = frame.copy()
        if r:
            start_time = time.time()

            # Only measure the time taken by YOLO and API Call overhead

            dark_frame = Image(frame)
            results = net.detect(dark_frame)
            del dark_frame

            end_time = time.time()
            # Frames per second can be calculated as 1 frame divided by time required to process 1 frame
            fps = 1 / (end_time - start_time)
            
            print("FPS: ", fps)
            print("Elapsed Time:",end_time-start_time)

            foundClasses = checkClassesFound(results)
            detectionWindow = detectionWindowPass()

            for cat, score, bounds in results:
                x, y, w, h = bounds
                cv2.rectangle(frame, (int(x-w/2),int(y-h/2)),(int(x+w/2),int(y+h/2)),(255,0,0))
                cv2.putText(frame, cat, (int(x), int(y)), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0))

                if (foundClasses and detectionWindow ):
                    print("Identified class")
                    filename = str(int(time.time()))
                    annotatedImagePath = output_path + filename + "_yolo3.jpg"
                    originalImagePath = output_path + filename + "_raw.jpg"
                    #cv2.imwrite(originalImagePath, original_frame)
                    cv2.imwrite(annotatedImagePath, frame)
                    csvUpdateFile(originalImagePath, annotatedImagePath, score, cat)

            #cv2.imshow("preview", frame)

        k = cv2.waitKey(1)
        if k == 0xFF & ord("q"):
            break
    cap.release()
