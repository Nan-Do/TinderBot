import pynder
import shutil
import requests
import json
import os.path
import threading
import Queue
import time

FBTOKEN = ""
FBID = ""

def MessageSender():
    headers = {"User-Agent": 'Tinder Android Version 3.2.1',
               "os-version": "19", 
               "app-version": "759", 
               "platform": "android", 
               "Content-type": "application/json; charset=utf-8"}
    def _(user_id, message):
        req = requests.post(
                'https://api.gotinder.com/user/matches/{}'.format(user_id),
                headers=headers,
                data=json.dumps({'message': message,
                                 'facebook_token': FBTOKEN, 
                                 'facebook_id': FBID}))
        return req.json()
    return _
    
     
class TinderSession():
    def __init__(self):
        self.FBTOKEN = FBTOKEN
        self.FBID = FBID
        
        self.session = pynder.Session(self.FBID, self.FBTOKEN)
        self.session_users = []
        self.session_matchs = []
        
        # Initialize the users queue
        self.users_queue = Queue.Queue()
        # Initialize the matchs queue
        self.matchs_queue = Queue.Queue()
        
        # Run the populating task queue for the first time
        self.users_thread = None
        self.__run_task_to_pupulate_users()
        
        self.matchs_thread = None
        self.__run_task_to_populate_matchs()
        
    def id(self):
        return pynder.Profile.id
        
    def __run_task_to_pupulate_users(self):
        users = self.session.nearby_users()
        self.users_thread = threading.Thread(target=self.__populate_users_queue, args=(users,))
        self.users_thread.start()
        
    def __run_task_to_populate_matchs(self):
        matchs = self.session.matches()
        self.matchs_thread = threading.Thread(target=self.__populate_matchs_queue, args=(matchs,))
        self.matchs_thread.start()
        
    def __populate_users_queue(self, users):
        for user in users:
            image_paths = []
            
            for num, photo in enumerate(user.photos, start=1):
                r = requests.get(photo, stream=True)
                name = user.name + "-" +  user.id + "-" + str(num)
                img_path = "images/" + name + ".jpg"
                print "Downloading " + name 
                with open(img_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                image_paths.append(img_path)
         
            user.image_paths = image_paths
            self.session_users.append(user)
            self.users_queue.put(user)
            time.sleep(0.2)
            
    def __populate_matchs_queue(self, matchs):
        self.session_matchs = []
        for match in matchs:
            image_paths = []
            
            for num, photo in enumerate(match.photos, start=1):
                name = match.name + "-" +  match.id + "-" + str(num)
                img_path = "images/" + name + ".jpg"
                if not os.path.exists(img_path):
                    r = requests.get(photo, stream=True)
                    print "Downloading (match)" + name
                    with open(img_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    
                image_paths.append(img_path)
             
            match.image_paths = image_paths                
            self.session_matchs.append(match)
            #self.matchs_queue.put(match)
            time.sleep(0.2)
            
    def find_nearby_user(self, identifier):
        try:
            return filter(lambda x: x.id == identifier, self.session_users)[0]            
        except IndexError:
            return None
            
    def get_user_name(self):
        return self.session.profile.name
            
    def get_nearby_user(self):
        # If the queue is empty and the thread is not running we have to rerun the thread again
        # otherwise the app will block forever
        if self.users_queue.empty() and not self.users_thread.is_alive():
            self.__run_task_to_pupulate_users()
            
        return self.users_queue.get()
    
    #def get_match(self):
    #    if self.matchs_queue.empty() and not self.matchs_thread.is_alive():
    #        self.__run_task_to_populate_matchs()
    #        
    #    return self.matchs_queue.get()
    
    def get_all_matches(self):
        if self.matchs_thread.is_alive():
            self.matchs_thread.join()
            
        return self.session_matchs
    
    def update_matches(self):
        if self.matchs_thread.is_alive():
            self.matchs_thread.join()
            
        self.__run_task_to_populate_matchs()
                    
#     def __update_users(self):
#         self.users = self.session.nearby_users()
#         
#     def __get_tinder_user(self):
#         while 1:
#             if len(self.users) == 0:
#                 self.__update_users()
#             
#             user = self.users.pop(0)
#             image_paths = []
#             for num, photo in enumerate(user.photos, start=1):
#                 r = requests.get(photo, stream=True)
#                 name = user.name + "-" +  user.id + "-" + str(num)
#                 img_path = "images/" + name + ".jpg"
#                 print "Downloading " + name 
#                 with open(img_path, 'wb') as f:
#                     shutil.copyfileobj(r.raw, f)
#                 image_paths.append(img_path)
#          
#             user.image_paths = image_paths        
#             yield user
#             
#     def get_tinder_user(self):
#         return self.__get_tinder_user().next()
