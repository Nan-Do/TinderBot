import os.path
import webapp2, jinja2, webapp2_static
import threading
from textblob import TextBlob

import Utils

from paste import httpserver
from TinderSession import TinderSession
from FaceExtractor import FaceExtractor
from EigenClassifier import EigenFaceClassifier
from DataBaseManager import DataBase
from TaskLogger import TaskLogger
from Bot import Bot
 
jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

db = taskLogger = tinderSession = eigenFaceClassifier = bot = None

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        t = jinja_environment.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        
class EvaluateUserHandler(Handler):
    def get(self):
        user_data = tinderSession.get_nearby_user()
        db.addUserToTheDatabase(user_data)
        
        common_friends = "No friends in common"
        if len(user_data.common_friends):
            common_friends = "|".join(user_data.common_friends)
            
        model_trained = eigenFaceClassifier.ready()
        
        self.render('evaluate_user.html', 
                    name=user_data.name,
                    age=user_data.age,
                    bio=user_data.bio,
                    image_paths=user_data.image_paths,
                    distance=user_data.distance,
                    distance_unit=user_data.distance_unit,
                    ping_time=user_data.ping_time,
                    common_friends=common_friends,
                    id=user_data.id,
                    model_trained=model_trained,
                    yes=Utils.YES,
                    no=Utils.NO)

class WebappHandler(Handler):
    def get(self):
        self.render('index.html')
        
        
class InboxHandler(Handler):
    def get(self, identifier):
        match = None
        matches = tinderSession.get_all_matches()
        if identifier:
            match = filter(lambda x: x.id == identifier, matches)[0]
            
        # Check if we got a new message from one of our matches
        for m in matches:
            m.new_activity = False
            if len(m.messages) == 0 or m.messages[-1].sender.name != tinderSession.get_user_name():
                m.new_activity = True
        
        if match:
            messages = []
            for m in match.messages:
                message = {}
                
                message['body'] = m.body
                                
                if m.sender.name == tinderSession.get_user_name():
                    message['sender'] = 'You'
                    message['polarity'] = 'none'
                else:
                    message['sender'] = m.sender
                    
                    blob = TextBlob(m.body)
                    res = 0
                    for sentence in blob.sentences:
                        #print "Polarity:", sentence.sentiment.polarity
                        res += sentence.sentiment.polarity
                        
                    #print "Total polarity:", res
                    if res > 0.0:
                        message['polarity'] = 'positive'
                    elif res < 0.0: 
                        message['polarity'] = 'negative'
                    else:
                        message['polarity'] = 'neutral'
                
                messages.append(message)
                
            self.render('inbox.html', matches=matches, messages=messages)
        else:
            self.render('inbox.html', matches=matches)
        
        
class MatchsHandler(Handler):
    def get(self):
        match = tinderSession.get_match()
        
        common_friends = "No friends in common"
        if len(match.common_friends):
            common_friends = "|".join(match.common_friends)
        
        self.render('match.html', 
                    name=match.name,
                    age=match.age,
                    bio=match.bio,
                    image_paths=match.image_paths,
                    distance=match.distance,
                    ping_time=match.ping_time,
                    common_friends=common_friends)
    
class UsersHandler(Handler):
    def get(self):
        users = db.getAllUsers(["id", "name", "age", "image_paths"])
        
        render_users = []
        
        for user in users:
            render_user = {}
            render_user['id'] = user[0]
            render_user['name'] = user[1]
            render_user['age'] = user[2]
            render_user['picture'] = user[3].split('|')[0]
            
            render_users.append(render_user)
            
        self.render('all_users.html', users=render_users)
    

class UserHandler(Handler):
    def get(self, identifier):
        user = db.getUser(identifier, ["name", "age", "bio", "image_paths", "distance", "distance_unit", "ping_time", "common_friends", "decision"])
        
        if user:
            common_friends = "No friends in common"
            if len(user[7]):
                common_friends = user[7]
                
            new = Utils.NO
            if user[7] == Utils.NO:
                new = Utils.YES
                
            self.render('user.html',
                        id=identifier,
                        name=user[0],
                        age=user[1],
                        bio=user[2],
                        image_paths=user[3].split('|'),
                        distance=user[4],
                        distance_unit=user[5],
                        ping_time=user[6],
                        common_friends=common_friends,
                        decision=user[8],
                        new=new)
        else:
            self.response.out.write("User doesn't exist")
        
    
class ProcessUserHandler(Handler):
    def post(self, identifier):
        name, paths =  db.getUser(identifier, ["name", "image_paths"])
        decision = self.request.get('select_button')
        
        # Update the decision in the database
        db.updateUserSelection(identifier, decision)
        
        # Let tinder know our decision about the user
        user = tinderSession.find_nearby_user(identifier)
        print "User found", user.id
        if decision == Utils.YES:
            taskLogger.addTask('User selected', user.id)
        #    user.like()
        else:
            taskLogger.addTask('User discarded', user.id)
        #    user.dislike()
            
        # Update the model
        eigenFaceClassifier.update_model(name, identifier, paths.split('|'), decision)
        db.updateUserSelection(user.id, decision)
        
        self.redirect('/evaluate_user')
            
            
class LoggerHandler(Handler):
    def get(self):
        start = self.request.get('start')
        if start: start = int(start)
        else: start = 0
            
        log_actions = taskLogger.getTasks(start)
        
        prev_q = (start != 0)
        next_q = (start + 50 < taskLogger.totalMessages())
        prev_val = start - 50
        next_val = start + 50
        
        self.render('log.html', 
                    log_actions = log_actions,
                    prev_q = prev_q,
                    next_q = next_q,
                    prev_val = prev_val,
                    next_val = next_val)
        
class PredictUserHandler(Handler):
    def get(self):
        user_data = tinderSession.get_nearby_user()
        db.addUserToTheDatabase(user_data)
        
        prediction=eigenFaceClassifier.predict(user_data.name, user_data.id, user_data.image_paths)
        print prediction
        
        common_friends = "No friends in common"
        if len(user_data.common_friends):
            common_friends = "|".join(user_data.common_friends)
        
        self.render('user.html', 
                    name=user_data.name,
                    age=user_data.age,
                    bio=user_data.bio,
                    image_paths=user_data.image_paths,
                    distance=user_data.distance,
                    ping_time=user_data.ping_time,
                    common_friends=common_friends,
                    prediction=prediction[0],
                    prediction_message=prediction[1])
        
class ChangeDecisionHandler(Handler):
    def post(self, identifier):
        new_decision = self.request.get('new_decision')
        db.updateUserSelection(identifier, new_decision)
        taskLogger.addTask('User changed decision', identifier)
        self.redirect('/user/' + identifier)


app = webapp2.WSGIApplication([
    ('/', WebappHandler),
    ('/evaluate_user/?', EvaluateUserHandler),
    ('/predict_user/?', PredictUserHandler),
    ('/users/?', UsersHandler),
    ('/user/?(.+)?', UserHandler),
    ('/process_user/?(.+)?', ProcessUserHandler),
    ('/match/?', MatchsHandler),
    ('/inbox/?(.+)?', InboxHandler),
    ('/log/?', LoggerHandler),
    ('/change_decision/?(.+)?', ChangeDecisionHandler),
    # Add the static route for the images
    ('/images/(.+)', webapp2_static.StaticFileHandler)
], debug=True, config = {'webapp2_static.static_file_path': './images'})

def main():
    # Run the server
    #httpserver.serve(app, host='192.168.1.11', port='8080')
    httpserver.serve(app, host='127.0.0.1', port='8080')

if __name__ == '__main__':
    # Check if the database doesn't exist and in that case
    # initialize it
    print "Running main"
    db = DataBase()
    taskLogger = TaskLogger(db)
    tinderSession = TinderSession()
    eigenFaceClassifier = EigenFaceClassifier(FaceExtractor())
    
    t1 = threading.Thread(target=main)
    t2 = threading.Thread(target=Bot, args=[db, 
                                            tinderSession, 
                                            eigenFaceClassifier, 
                                            taskLogger])
    
    t1.start(); t2.start()
    t1.join(); t2.join()
