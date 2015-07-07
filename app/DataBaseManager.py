import os
import sqlite3

import Utils

DB_PATH = Utils.DATA_PATH + 'usersdb.sqlite'

class DataBase(object):
    def __init__(self):
        self.db = None
        
        if not os.path.exists(DB_PATH):
            # Create table
            self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
            print "Creating the tables"
            self.db.execute('''CREATE TABLE IF NOT EXISTS
                                  users(id TEXT PRIMARY KEY, 
                                        name TEXT, 
                                        age INTEGER, 
                                        bio TEXT, 
                                        image_paths TEXT unique, 
                                        common_friends TEXT,
                                        common_likes TEXT,
                                        distance INTEGER,
                                        distance_unit TEXT,
                                        url_photos TEXT,
                                        ping_time TEXT,
                                        birth_date DATE,
                                        decision TEXT)''')
            
            self.db.execute('''CREATE TABLE IF NOT EXISTS
                                logs (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      timestamp INTEGER,
                                      message TEXT,
                                      user_id TEXT)''')
            
        else:
            self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
            
    def addLogMessageToTheDatabase(self, timestamp, message, user_id):
        cursor = self.db.cursor()
        params = (timestamp, message, user_id)
        
        cursor.execute("INSERT INTO logs VALUES(NULL, ?, ?, ?)", params)
        

    def getLogMessages(self, first=0, last=0):
        cursor = self.db.cursor()
        if first==0 and last==0:
            log_messages = cursor.execute("SELECT * from logs")
        else:
            log_messages = cursor.execute("SELECT * from logs WHERE id>=? AND id<?", (first, last))
            
        return log_messages
    
    def getTotalLogMesagges(self):
        cursor = self.db.cursor()
        total = cursor.execute("SELECT COUNT(*) from logs").fetchone()[0]
        return total
            
    def addUserToTheDatabase(self, user_data):
        # Insert a row of data
        cursor = self.db.cursor()
        params = (user_data.id,
                  user_data.name,
                  user_data.age,
                  user_data.bio,
                  "|".join(user_data.image_paths),
                  "|".join(user_data.common_friends),
                  "|".join(user_data.common_likes),
                  user_data.distance,
                  user_data.distance_unit,
                  "|".join(user_data.photos),
                  user_data.ping_time,
                  user_data.birth_date,
                  Utils.NO
                  )
        try:
            cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
            # Save (commit) the changes
            self.db.commit()
        except sqlite3.IntegrityError:
            pass
        
    def updateUserSelection(self, identifier, decision):
        query = "UPDATE USERS SET decision=\"{0}\" WHERE id=\"{1}\";".format(decision, identifier)
        print query
        cursor = self.db.cursor()
        cursor.execute(query)        
        
    def getAllUsers(self, elements=None):
        cursor = self.db.cursor()
        if elements:
            users = cursor.execute("SELECT " + ",".join(elements) + " from USERS").fetchall()
        else:
            users = cursor.execute("SELECT * from USERS")
        return users
    
    def getUser(self, identifier, elements=None):
        cursor = self.db.cursor()
        
        if elements:
            query = "SELECT " + ", ".join(elements) + " from USERS where id = \"{0}\";".format(identifier)
            print query
            user = cursor.execute(query).fetchone()
        else:
            user = cursor.execute("SELECT * from USERS where id = {0};".format(identifier))
            
        return user