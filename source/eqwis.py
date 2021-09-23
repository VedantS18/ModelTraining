
import torch
import numpy as np
import cv2
from time import time
from datetime import datetime
import csv
import os


class ObjectDetection:
    """
    Class implements Yolo5 model to make inferences on a RTSP video stream using Opencv2.
    """

    def __init__(self, rtsp):
        """
        Initializes the class with youtube url and output file.
        :param url: Has to be as youtube URL,on which prediction is made.
        :param out_file: A valid output file name.
        """
        self.last_detection_time = None
        self.output_path = "./output/"
        self.detection_window_threshold = 5
        self._RTSP = rtsp
        self.model = self.load_model()
        self.classes = self.model.names
        self.out_file = out_file
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.writer = None
        self.file = None
        #metadata file
        self.csv_file_path = "./output/metadata.csv"

        print(self.device)

        #categories to look for
        self.categories = ["sheep", "horse", "cow", "dog", "person"]
        self.confidence_threshold = 0.2

    def open_metadata_file(self) :        
        #create the required directory structure
        if (os.path.isdir(self.output_path) == False):
            os.mkdir(self.output_path)
        if(os.path.isfile(self.csv_file_path) == True):
            with open(self.csv_file_path, 'a', newline = '') as self.file:
                self.writer = csv.writer(self.file)
        else:
            with open(self.csv_file_path, 'w', newline = '') as self.file:
                self.writer = csv.writer(self.file)
                self.writer.writerow(["Timestamp", "OriginalImagePath", "AnnotatedImagePath", "Confidence"])

    def get_video_from_url(self):
        """
        Creates a new video streaming object to extract video frame by frame to make prediction on.
        :return: opencv2 video capture object, with lowest quality frame available for video.
        """   
        return cv2.VideoCapture(self._RTSP)    
    
    def load_model(self): 
        """
        Loads Yolo5 model from pytorch hub.
        :return: Trained Pytorch model.
        """
        model = torch.hub.load('/yolov5/standard', 'custom', '/yolov5/standard/yolov5s.pt', source = 'local', force_reload=True)
        return model

    def score_frame(self, frame):
        """
        Takes a single frame as input, and scores the frame using yolo5 model.
        :param frame: input frame in numpy/list/tuple format.
        :return: Labels and Coordinates of objects detected by model in the frame.
        """
        self.model.to(self.device)
        frame = [frame]
        results = self.model(frame)
        labels, cord = results.xyxyn[0][:, -1].cpu().detach().numpy(), results.xyxyn[0][:, :-1].cpu().detach().numpy()
        print(labels)
        return labels, cord

    def class_to_label(self, x):
        """
        For a given label value, return corresponding string label.
        :param x: numeric label
        :return: corresponding string label
        """
        return self.classes[int(x)]

    def plot_boxes(self, _results, frame):
        """
        Takes a frame and its results as input, and plots the bounding boxes and label on to the frame.
        :param results: contains labels and coordinates predicted by model on the given frame.
        :param frame: Frame which has been scored.
        :return: Frame with bounding boxes and labels ploted on it.
        """
        labels, cord = _results
        n = len(labels)
        x_shape, y_shape = frame.shape[1], frame.shape[0]
        for i in range(n):
            row = cord[i]
            if row[4] >= 0.2:
                x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
                bgr = (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                cv2.putText(frame, self.class_to_label(labels[i]), (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)

        return frame

    def detection_window_passed(self) :
        if (self.last_detection_time == None) :
            self.last_detection_time = time()

        current_detection_time = time()
        if (current_detection_time - self.last_detection_time > self.detection_window_threshold) :
            self.last_detection_time = current_detection_time
            return True
        return False

    def check_interest_categories(self, _results) :
        labels, cord = _results
        n = len(labels)
        for i in range(n):
            row = cord[i]
            if row[4] >= self.confidence_threshold:
                label = self.class_to_label(labels[i])
                if (label in self.categories) :
                    return True
        return False

    def update_metadata_file(self, _originalImagePath, _annotatedImagePath, _confidence, category):
        """
        #Register metadata into csv with format "Date", "Time", "OriginalImagePath", "AnnotatedImagePath", "Confidence"
        """
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        if(category in self.categories):     
            if(os.path.isfile(self.csv_file_path) == True):
                with open(self.csv_file_path, 'a', newline = '') as self.file:
                    self.writer = csv.writer(self.file)
                    self.writer.writerow([dt_string, _originalImagePath, _annotatedImagePath, _confidence, category])
            else:
                with open(csv_file_path, 'w', newline = '') as self.file:
                    self.writer = csv.writer(self.file)
                    self.writer.writerow(["Timestamp", "OriginalImagePath", "AnnotatedImagePath", "Confidence", "Category"])
                    self.writer.writerow([dt_string, _originalImagePath, _annotatedImagePath, _confidence])
            self.file.close()

    def register_write_detections(self, _results, _frame) :
        labels, cord = _results
        n = len(labels)
        for i in range(n):
            confidence = cord[i][4]
            label = self.class_to_label(labels[i])
            if confidence >= self.confidence_threshold and (label in self.categories):
                original_frame = _frame.copy()
                _frame = self.plot_boxes(_results, _frame)
                filename = str(int(time()))
                detectionsImagePath = self.output_path + filename + "_yolov5.jpg"
                originalImagePath = self.output_path + filename + "_raw.jpg"
                cv2.imwrite(originalImagePath, original_frame)
                cv2.imwrite(detectionsImagePath, _frame)
                self.update_metadata_file(originalImagePath, detectionsImagePath, confidence, label)

    def __call__(self):
        """
        This function is called when class is executed, it runs the loop to read the video frame by frame,
        and write the output into a new file.
        :return: void
        """ 
        self.open_metadata_file()
        frame_rate = 1.5 #fps
        player = self.get_video_from_url()
        assert player.isOpened()
        four_cc = cv2.VideoWriter_fourcc(*"MJPG")
        prev = time()
        while True:
            #check for detection of horses and set the flag save the metadata
            foundClasses = False;
            start_time = time()
            time_elapsed = start_time - prev
            ret, frame = player.read()
            if time_elapsed > 1./frame_rate:
                if ret:
                 
                    results = self.score_frame(frame)

                    end_time = time()
                    fps = 1. / np.round(end_time - start_time, 3)

                    found_classes_of_interest = self.check_interest_categories(results)
                    detection_window_met = self.detection_window_passed()

                    if (found_classes_of_interest and detection_window_met):
                        self.register_write_detections(results, frame)
                prev = time()
            k = cv2.waitKey(1)
            if k == 0xFF & ord("q"):
                break

# Create a new object and execute.
a = ObjectDetection('rtsp://admin:M*ttapalli8*@191.168.86.6/unicast/c1/s0/live')
a()