from pymongo import MongoClient


class MongoDB:
    def __init__(self, database_name):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client[database_name]

    def insert_one(self, o, collection):
        try:
            collection = self.db[collection]
            collection.insert_one(o)
        except Exception as e:
            print(e)

    def update_one(self, obj_match, obj_update, collection):
        try:
            self.db[collection].update_one(obj_match, obj_update)
        except Exception as e:
            print(e)

    def delete_one(self, obj, collection):
        try:
            self.db[collection].delete_one(obj)
        except Exception as e:
            print(e)

    def find_one(self, obj, collection):
        try:
            return self.db[collection].find_one(obj)
        except Exception as e:
            print(e)
            return None

    def find(self, o, collection, limit):
        collection = self.db[collection]
        cursor = collection.find(o).limit(limit)
        return cursor