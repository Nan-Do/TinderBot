'''
Created on Mar 4, 2015

@author: nando
'''

import cv2

class FaceExtractor(object):
    def __init__(self,
                 height=240,
                 width=240,
                 savePath="faces/",
                 cascPath="../haarcascade_frontalface_default.xml"):
        
        self.height = height
        self.width = width
        self.savePath = savePath
        self.faceCascade = cv2.CascadeClassifier(cascPath)
        
        self.file_name_prefix = None
        self.imagePaths = None
        
    def setUserData(self, name, user_id, imagePaths):
        self.filename_prefix = name + "-" +  user_id 
        self.imagePaths = imagePaths
        
        
    def obtainFacesPathsForPrediction(self):
        facePaths = []
        
        for imageNum, imagePath in enumerate(self.imagePaths, start=1):
            # Load the picture and extract the faces
            try:
                image = cv2.imread(imagePath, 0)
            except UnicodeEncodeError:
                continue
                
            faces = self.faceCascade.detectMultiScale(
                image,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(30, 30),
                flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
            
            print "Image loaded"
            
            if len(faces) > 1:
                print "Warning image", self.filename_prefix + "-" + str(imageNum), "contains more than one face not including for prediction"
                continue
            if len(faces) == 0:
                print "Warning image", self.filename_prefix + "-" + str(imageNum), "doesn't include a detected face not including for prediction"
                continue
                
            (x, y, w, h) = faces[0]
            face = image[y:(y+h), x:(x+w)]
            resized_face = cv2.resize(face, (self.width, self.height))
            face_fname = self.savePath + self.filename_prefix + "-" + str(imageNum) + "-Face-1.jpg"
                
            facePaths.append(face_fname)
            cv2.imwrite(face_fname, resized_face)
            
        return facePaths
        
    def obtainFacesPaths(self):
        facePaths = []
        
        for imageNum, imagePath in enumerate(self.imagePaths, start=1):
            # Load the picture and extract the faces
            try:
                image = cv2.imread(imagePath, 0)
            except UnicodeEncodeError:
                continue
                
            faces = self.faceCascade.detectMultiScale(
                image,
                scaleFactor=1.3,
                minNeighbors=6,
                minSize=(30, 30),
                flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
            
            if len(faces) == 0:
                print "Warning image", self.filename_prefix + "-" + str(imageNum), "doesn't contain any face"
                
            if len(faces) > 1:
                print "Warning image", self.filename_prefix + "-" + str(imageNum), "contains more than one face"
            
            for faceNum, (x, y, w, h) in enumerate(faces, start=1):
                face = image[y:(y+h), x:(x+w)]
                resized_face = cv2.resize(face, (self.width, self.height))
                face_fname = self.savePath + self.filename_prefix + "-" + str(imageNum) + "-Face-" + str(faceNum) +  ".jpg"
                
                facePaths.append(face_fname)
                cv2.imwrite(face_fname, resized_face)
                
        return facePaths