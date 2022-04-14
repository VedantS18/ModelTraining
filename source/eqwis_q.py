
import torch
import numpy as np
import cv2
from time import time
from datetime import datetime
import csv
import os
import queue
import threading

class ObjectDetection:
    """
    Class implements Yolo5 model to make inferences on a RTSP video stream using Opencv2.
    """

    def __init__(self, rtsp, rtsp_t):

        now = datetime.now()
        self.last_detection_time = None
        self.datepath = now.strftime("%d_%m_%y")
        self.baseline_path = "/yolov5/baseline/" + self.datepath + "/"
        self.output_path = "/yolov5/output/" + self.datepath + "/"
        self.detection_window_threshold = 5
        self._RTSP = rtsp
        self._RTSP_t = rtsp_t
        self.model = self.load_model()
        self.classes = self.model.names
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.writer = None
        self.file = None
        #metadata file
        self.csv_file_path = self.output_path + "metadata.csv"
        self.optical_q = queue.Queue()
        self.thermal_q = queue.Queue()
        print(self.device)

        #categories to look for
        self.categories = ["sheep", "horse", "cow", "dog", "person"]
        self.confidence_threshold = 0.5

        # cv2a.videoio_registry.getBackends() returns list of all available backends.
        availableBackends = [cv2.videoio_registry.getBackendName(b) for b in cv2.videoio_registry.getBackends()]
        print(availableBackends)



    def open_metadata_file(self) :        
        #create the required directory structure
        if (os.path.isdir(self.output_path) == False):
            os.mkdir(self.output_path)

        if (os.path.isdir(self.baseline_path) == False):
            os.mkdir(self.baseline_path)

        if(os.path.isfile(self.csv_file_path) == True):
            with open(self.csv_file_path, 'a', newline = '') as self.file:
                self.writer = csv.writer(self.file)
        else:
            with open(self.csv_file_path, 'w', newline = '') as self.file:
                self.writer = csv.writer(self.file)
                self.writer.writerow(["Timestamp", "OriginalImagePath", "AnnotatedImagePath", "Confidence"])

    def get_video_from_optical(self):
        """
        Creates a new video streaming object to extract video frame by frame to make prediction on.
        :return: opencv2 video capture object, with lowest quality frame available for video.
        """   
        cap = cv2.VideoCapture(self._RTSP, cv2.CAP_FFMPEG)   
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
        return cap
         
    def get_video_from_thermal(self):
        return cv2.VideoCapture(self._RTSP_t)  
    
    
    def load_model(self): 
        """
        Loads Yolo5 model from pytorch hub.
        :return: Trained Pytorch model.
        """
        #model = None
        model = torch.hub.load('./', 'custom', './yolov5s.pt', source = 'local', force_reload=True)
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
            conf = cord[i][4]
            if row[4] >= 0.2:
                x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
                bgr = (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                cv2.putText(frame, self.class_to_label(labels[i]) + str(conf), (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)

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

    def register_write_detections(self, _results, _frame, _filename, _subscript) :
        labels, cord = _results
        n = len(labels)
        for i in range(n):
            confidence = cord[i][4]
            label = self.class_to_label(labels[i])
            if confidence >= self.confidence_threshold and (label in self.categories):
                original_frame = _frame.copy()
                _frame = self.plot_boxes(_results, _frame)
                detectionsImagePath = self.output_path + _filename + _subscript + "_yolov5.jpg"
                originalImagePath = self.output_path + _filename + _subscript + "_raw.jpg"
                cv2.imwrite(originalImagePath, original_frame)
                cv2.imwrite(detectionsImagePath, _frame)
                self.update_metadata_file(originalImagePath, detectionsImagePath, confidence, label)

    def register_baseline_frame(self, _frame, _filename, _subscript):
        baselineImagePath = self.output_path + _filename + _subscript + "_baseline.jpg"
        cv2.imwrite(baselineImagePath, _frame)

    def receive_frames(self):
        frame_rate = 1.0
        player_o = self.get_video_from_optical()
        player_t = self.get_video_from_thermal()
        assert player_o.isOpened()
        assert player_t.isOpened()
        prev = time()
        while True:
            assert player_o.isOpened()
            assert player_t.isOpened()
            start_time = time()
            time_elapsed = start_time - prev
            ret_o, frame_o = player_o.read()
            ret_t, frame_t = player_t.read()
            if time_elapsed > 1./frame_rate:
                print("Time Qualified")
                print(ret_o)
                print(ret_t)       
                if ret_o and self.optical_q.empty():
                    print("Queueing O Frames")
                    self.optical_q.put(frame_o)
                else :
                    player_o.release();
                    player_o = self.get_video_from_optical()
                if ret_t and self.thermal_q.empty():
                    print("Queueing T Frames")
                    self.thermal_q.put(frame_t)
                else :
                    player_t.release();
                    player_t = self.get_video_from_thermal()
                if ret_o or ret_t :
                    end_time = time()
                    prev = end_time
                    
    def process_optical(self):
        drop_time = 30.0 #every 30 seconds
        prev_drop_time = time()
        while True:
            #check for detection of horses and set the flag save the metadata
            foundClasses = False;
            if self.optical_q.empty() != True:
                frame = self.optical_q.get()
                print("Processing O Frame")
                filename = str(int(time()))
                results = self.score_frame(frame)

                if (time() - prev_drop_time > drop_time):
                    self.register_baseline_frame(frame, filename,"_o")
                    prev_drop_time = time()

                found_classes_of_interest = self.check_interest_categories(results)
                detection_window_met = self.detection_window_passed()

                if (found_classes_of_interest and detection_window_met):
                    self.register_write_detections(results, frame, filename, "_o")
                    print("Found classes of interest")
    
    def process_thermal(self):
        drop_time = 30.0 #every 30 seconds
        prev_drop_time = time()
        while True:
            #check for detection of horses and set the flag save the metadata
            foundClasses = False;
            if self.thermal_q.empty() != True:
                frame = self.thermal_q.get()
                print("Processing T Frame")
                filename = str(int(time()))                
                results = self.score_frame(frame)

                if (time() - prev_drop_time > drop_time):
                    self.register_baseline_frame(frame, filename,"_t")
                    prev_drop_time = time()


                found_classes_of_interest = self.check_interest_categories(results)
                detection_window_met = self.detection_window_passed()

                if (found_classes_of_interest and detection_window_met):
                    self.register_write_detections(results, frame, filename, "_t")
                    print("Found classes of interest")
           
                           
                    
    
    def __call__(self):
        """
        This function is called when class is executed, it runs the loop to read the video frame by frame,
        and write the output into a new file.
        :return: void
        """ 
        self.open_metadata_file()
        p1 = threading.Thread(target=self.receive_frames)
        p1.start()
        p3 = threading.Thread(target=self.process_optical)
        p3.start()
        p4 = threading.Thread(target=self.process_thermal)
        p4.start()

a = ObjectDetection('rtsp://admin:Eqwis1234@192.168.1.64/Streaming/Channels/101', 'rtsp://admin:Eqwis1234@192.168.1.64/Streaming/Channels/201')
a()
