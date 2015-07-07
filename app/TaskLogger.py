'''
Created on Mar 16, 2015

@author: nando
'''

import time

from datetime import datetime
from collections import namedtuple
from threading import Lock

Task = namedtuple('Task', ['time', 'action', 'user_id'])

class TaskLogger(object):
    def __init__(self, database):
        #self.tasks = []
        self.database = database
        self.lock = Lock()
        
        self.total = database.getTotalLogMesagges()
        
    def totalMessages(self):
        return self.total
    
    def addTask(self, action, user_id):
        self.lock.acquire()
        ts = time.time()
        #self.tasks.append(Task(ts, datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), action, user_id))
        self.database.addLogMessageToTheDatabase(ts, action, user_id)
        self.total += 1
        self.lock.release()
        
    def getTasks(self, first=0, total=50):
        #return self.tasks
        tasks = []
        for task in self.database.getLogMessages(first, first+total):
            print task
            tasks.append(Task(datetime.fromtimestamp(task[1]).strftime('%Y-%m-%d %H:%M:%S'), task[2], task[3]))
            
        return tasks