import ConfigParser
import time, random

import Utils

from TinderSession import MessageSender
from textblob import TextBlob
from pyDatalog.pyDatalog import assert_fact, load, ask, retract_fact, Logic

class LogicRuleEngine(object):
    def __init__(self, rulesPath='../user.rules'):
        Logic()
        with open(rulesPath, 'r') as f:
            rules = "\n".join(f.readlines())
            
        load(rules)
        print "Rules for the user loaded"
        print rules
        
    def __assert_user(self, user, prediction):
        assert_fact('user_id', user.id)
        assert_fact('name', user.id, user.name)
        assert_fact('age', user.id, user.age)
        assert_fact('bio', user.id, user.bio)
        assert_fact('distance', user.id, user.distance)
        assert_fact('distance_unit', user.id, user.distance_unit)
        assert_fact('ping_time', user.id, user.ping_time)
        assert_fact('birth_date', user.id, user.birth_date)
        
        for friend in user.common_friends:
            assert_fact('common_friend', user.id, friend)
            
        for like in user.common_likes:
            assert_fact('common_likes', user.id, like)
            
        assert_fact('prediction', user.id, prediction)
        
    def __retract_user(self, user, prediction):
        retract_fact('user_id', user.id)
        retract_fact('name', user.id, user.name)
        retract_fact('age', user.id, user.age)
        retract_fact('bio', user.id, user.bio)
        retract_fact('distance', user.id, user.distance)
        retract_fact('distance_unit', user.id, user.distance_unit)
        retract_fact('ping_time', user.id, user.ping_time)
        retract_fact('birth_date', user.id, user.birth_date)
        
        for friend in user.common_friends:
            retract_fact('common_friend', user.id, friend)
            
        for like in user.common_likes:
            retract_fact('common_likes', user.id, like)
            
        retract_fact('prediction', user.id, prediction)
        
    def analize_user(self, user, prediction):
        actions = []
        self.__assert_user(user, prediction)
        
        if ask('accept("{}")'.format(str(user.id))) != None:
            actions.append('Accept')
        else:
            actions.append('Reject')
            
        #if ask('log("{}")'.format(str(user.id))) != None:
        #    actions.append('Log')
            
        return actions
        
    

class AcceptationTask(object):
    def __init__(self, database, engine, tinderSession, eigenClassifier, logger):
        self.engine = engine
        self.tinderSession = tinderSession
        self.eigenClassifier = eigenClassifier
        self.database = database
        self.logger = logger
        
    def __predict_user(self, user_name, user_id, user_image_paths):
        return self.eigenClassifier.predict(user_name, user_id, user_image_paths)
        
        
    def is_ready(self, elapsed):
        if (elapsed % 60) == 0 and self.eigenClassifier.ready():
            return True
        return False
        
    def run(self):
        user = self.tinderSession.get_nearby_user()
        self.database.addUserToTheDatabase(user)
        
        prediction = self.__predict_user(user.name, user.id, user.image_paths)
                
        if prediction[0] == Utils.YES:
            self.database.updateUserSelection(user.id, Utils.YES)
            self.logger.addTask('Bot predicted a yes for user:', user.id)
        else:
            self.database.updateUserSelection(user.id, Utils.NO)
            self.logger.addTask('Bot predicted a no (' + prediction[1] + ') for user:', 
                                user.id)
        print 'Prediction of user:' + prediction[0], user.id
        
        actions_for_user = self.engine.analize_user(user, prediction[0])
        
        for action in actions_for_user:
            if action == "Accept":
                self.logger.addTask('Bot accepting user:', user.id)
                print 'Accepted user:', user.id
                user.like()
            if action == "Reject":
                self.logger.addTask('Bot rejecting user:', user.id)
                print 'Rejected user:', user.id
                user.dislike()

            if action == "Log":
                self.logger.addTask('Bot loggin user:', user.id)
        
class ChatTask(object):
    def __init__(self, database, tinderSession, eigenClassifier, logger, conversationsPath='../conversations.ini'):
        self.tinderSession = tinderSession
        self.eigenClassifier = eigenClassifier
        self.database = database
        self.logger = logger
        
        self.conversations = []
        self.message_sender = MessageSender()
        
        # Build the dictionary of conversations
        config = ConfigParser.ConfigParser()
        config.read([conversationsPath])
        for section_name in config.sections():
            conv = {}
            for name, value in config.items(section_name):
                conv[name] = value
            self.conversations.append(conv)
            print conv
    
    def __identify_conversation(self, sentence):
        for conversation in self.conversations:
            if conversation['first'] == sentence:
                return conversation
        return None
    
    def __compute_setiment_analsys(self, chat_message):
        blob = TextBlob(chat_message)
        res = 0
        
        for sentence in blob.sentences:
            res += sentence.sentiment.polarity
            
        if res > 0.0:
            return 'positive'
        elif res < 0.0:
            return 'negative'
        else:
            return 'neutral'
        
    def is_ready(self, elapsed):
        if (elapsed % 15) == 0:
            return True
        return False
        
    def run(self):
        matches = self.tinderSession.get_all_matches()
        
        for match in matches:
            message = None

            # If we don't have any messages choose one random first message and send it
            if len(match.messages) == 0:
                message = random.choice(self.conversations)['first']
            else:
                # We already sent all the required messages is the user who must send them now
                sent_messages = filter(lambda x: x.sender.name == self.tinderSession.get_user_name(), match.messages)
                if len(sent_messages) >= 3:
                    continue
                
                # Check we didn't send the last message
                last_message = match.messages[-1]
                if last_message.sender.name == self.tinderSession.get_user_name():
                    continue
                    
                # Check that the bot sent the first message.
                first_message = match.messages[0]
                if first_message.sender.name != self.tinderSession.get_user_name():
                    continue
                conversation = self.__identify_conversation(first_message.body)
                if not conversation:
                    continue
                
                sentiment = self.__compute_setiment_analsys(last_message.body)
                message = conversation[sentiment + '_' + str(len(sent_messages))]
                
            # We had a successful message
            print "User: " + match.id +  " Message: " + message 
            match.message(message)
            self.logger.addTask('Message sent: ' +  message, match.id)
            
class UpdateMatchesTask(object):
    def __init__(self, tinderSession):
        self.tinderSession = tinderSession
    
    def is_ready(self, elapsed):
        if (elapsed % 45) == 0:
            return True
        return False
    
    def run(self):
        self.tinderSession.update_matches()
        
    
class NotifyUserTask(object):
    def __init__(self):
        pass
    
    def is_ready(self, elapsed):
        return False
    
    def run(self):
        return

class Bot(object):
    def __init__(self,
                 database, 
                 tinderSession, 
                 eigenClassifier, 
                 logger):
        engine = LogicRuleEngine()
        classification = AcceptationTask(database, engine, tinderSession, eigenClassifier, logger)
        chat = ChatTask(database, tinderSession, eigenClassifier, logger)
        updateMatches = UpdateMatchesTask(tinderSession)
        
        self.tasks = [classification, chat, updateMatches]
        
        self.bot_running = False
        self.__bot_start()

    def __bot_start(self):
        self.bot_running = True
        self.__run_bot_tasks()
        
    def __run_bot_tasks(self):
        elapsed = 1
        time.sleep(10)
        while 1:
            for task in self.tasks:
                if task.is_ready(elapsed):
                    task.run()
            
            elapsed += 1
            if elapsed == 600: elapsed = 0
            
            time.sleep(1)