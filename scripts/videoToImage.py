#requirements: sudo apt install ffmpeg
#folder structure: ScriptDirectory, make the target directory before running the script
import cv2
import os
import subprocess
inputDirectory = "Folder path containing the videos"
targetDirectory = "Folder where extracted images will be kept"
fileName = ""
codeString = ""
fileNameList = os.listdir(inputDirectory)
splitFileName = ""
i= 0
while i < len(fileNameList):
	fileName = inputDirectory + fileNameList[i]
	imageCount = i + 1
	splitFileName = fileName.split(".")[0]
	codeString = "ffmpeg -i " + fileName + " -r (#frames)/(#seconds) " + splitFileName + "%03d.jpg"
	proc = subprocess.Popen(codeString, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	out, err = proc.communicate()
	i = i + 1



