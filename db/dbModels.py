from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
from properties import *
import string, random

uri_local = "mongodb://localhost:27017"
uri_web = db_uri
client = MongoClient(uri_web)
db = client['Aviel']
Users = db["Users"]
Logs = db["Logs"]


class UsersDb:
    def __init__(self):
        self.collection = Users
    
    def add_user(self, user):
        return self.collection.insert_one(user).inserted_id
    
    def get_user_by_id(self, user_id):
        return self.collection.find_one({"_id": ObjectId(user_id)})
    
    def get_user_by_username(self, username):
        return self.collection.find_one({"username": username})

class logsDb:
    def __init__(self):
        self.collection = Logs
    
    def add_log(self, log):
        return self.collection.insert_one(log).inserted_id
    
        