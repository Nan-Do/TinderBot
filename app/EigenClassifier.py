'''
Created on Mar 4, 2015

@author: nando
'''

import os.path
import threading

import cv2
import numpy as np

import Utils

YES=0
NO=1

REQUIRED_USERS = 45
MODEL_FILE = Utils.DATA_PATH + "EigenFaceClassifier.model"


class EigenFaceClassifier(object):
    def __init__(self, faceExtractor):
        self.model = cv2.createEigenFaceRecognizer(threshold=8250.0)
        self.faceExtractor = faceExtractor
        
        self.session_average_face_yes = None
        self.session_total_yes = 0
        self.session_average_face_no = None
        self.session_total_no = 0
        
        # To determine if the model is or has been trained
        self.scored_users = 0
        self.model_trained = False
        
        self.session_faces_model = []
        self.session_faces_labels = []
        
        self.previous_average_face_yes = None
        self.previous_average_face_no = None
        
        self.thread = None
        
        self.load_models()
        
    def __compute_average_face(self, session_average_face, session_totals, previous_average_face):
        average_face = None
        if session_average_face != None:
            average_face = session_average_face.astype(np.int32)
            average_face /= session_totals
            
        if previous_average_face != None:
            if session_average_face != None:
                average_face = (average_face + previous_average_face) / 2
            else:
                average_face = previous_average_face
            
        return average_face
    
    def ready(self):
        return (self.model_trained or self.scored_users >= REQUIRED_USERS)      
        
    def update_model(self, user_name, user_id, image_paths, decission):
        self.faceExtractor.setUserData(user_name, user_id, image_paths)
        face_paths = self.faceExtractor.obtainFacesPaths()
        
        self.scored_users += 1
        
        for face_path in face_paths:
            face = cv2.imread(face_path, cv2.IMREAD_GRAYSCALE)
            
            self.session_faces_model.append(np.asarray(face, dtype=np.uint8))
            
            if decission == Utils.YES:
                self.session_faces_labels.append(YES)
                self.session_total_yes += 1
                
                if self.session_average_face_yes != None:
                    self.session_average_face_yes += face
                else:
                    self.session_average_face_yes = face.astype(np.int32)
                
            else:
                self.session_faces_labels.append(NO)
                self.session_total_no += 1
                
                if self.session_average_face_no != None:
                    self.session_average_face_no += face
                else:
                    self.session_average_face_no = face.astype(np.int32)
                    
        if (self.scored_users % 5) == 0:
            #self.scored_users=0
            #self.save_models()
            self.__run_save_models_task()
            
            
    def __run_save_models_task(self):
        if self.thread != None and self.thread.is_alive():
            self.thread.join()
            
        self.thread = threading.Thread(target=self.save_models)
        self.thread.start()
                    
    def train(self):
        if len(self.session_faces_labels):
            self.model.train(self.session_faces_model,
                             np.asarray(self.session_faces_labels,
                                        dtype=np.int32))
        
    def save_models(self):
        print "Saving models"
        self.train()
        self.model.save(MODEL_FILE)
        
        if (not self.model_trained and self.scored_users >= REQUIRED_USERS):
            self.model_trained = True
            open(Utils.DATA_PATH + "model_trained", 'w').close()

        average_yes = self.__compute_average_face(self.session_average_face_yes, 
                                                  self.session_total_yes, 
                                                  self.previous_average_face_yes)
        cv2.imwrite(Utils.DATA_PATH + "average_face_yes.jpg", average_yes)
        
        average_no = self.__compute_average_face(self.session_average_face_no, 
                                                  self.session_total_no, 
                                                  self.previous_average_face_no)
        cv2.imwrite(Utils.DATA_PATH + "average_face_no.jpg", average_no)
        
        
    def load_models(self):
        print "Loading models"
        
        if os.path.exists(Utils.DATA_PATH + "average_face_yes.jpg"):
            print "Loading previous yes average face"
            self.previous_average_face_yes = cv2.imread(Utils.DATA_PATH + "average_face_yes.jpg", 
                                                        cv2.IMREAD_UNCHANGED)
        
        if os.path.exists(Utils.DATA_PATH + "average_face_no.jpg"):
            print "Loading previous no average face"
            self.previous_average_face_no = cv2.imread(Utils.DATA_PATH + "average_face_no.jpg", 
                                                       cv2.IMREAD_UNCHANGED)
        
        if os.path.exists(MODEL_FILE):
            print "Loading previous model"
            self.model.load(MODEL_FILE)
            
        if os.path.exists(Utils.DATA_PATH + "model_trained"):
            print "Model trained in a previous sesion"
            self.model_trained = True
        
    def predict(self, user_name, user_id, image_paths):
        self.faceExtractor.setUserData(user_name, user_id, image_paths)
        face_paths = self.faceExtractor.obtainFacesPathsForPrediction()
        predictions = []
        
        print face_paths
        # Some simple euristics to discard users with silly pictures
        if len(face_paths) == 0:
            return Utils.NO, "No faces were recognized"
        #if len(face_paths) < 2:
        #    return "No", "Not enough faces were found"
        #if len(face_paths) < (len(image_paths) / 2):
        #    return "No", "Sparse photos"
        
        for face_path in face_paths:
            face = cv2.imread(face_path, cv2.IMREAD_GRAYSCALE)
            [p_label, p_confidence] = self.model.predict(face)
            predictions.append(p_label)
            
        print predictions
            
        total_yes = sum(1 for x in predictions if x == YES)
        total_no = sum(1 for x in predictions if x == NO)
        
        if total_yes > total_no:
            return Utils.YES, "User matches the model"
        if total_yes == total_no:
            return Utils.UNKNOWN, "Not enough data to decide"
        else:
            return Utils.NO, "User doesn't match the model"
            
            
            
            
        

