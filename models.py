"""
This file contains models to be used as an ORM for the "caroline" database in MongoDB
"""

from mongoengine import Document, StringField, IntField, DictField, DateTimeField, BooleanField
import datetime


class Task(Document):
    meta = {'collection': 'tasks'}
    misc = DictField()
    c_id = IntField()
    command = StringField()
    log_file = StringField()
    work_dir = StringField()

    start_time = DateTimeField()
    end_time = DateTimeField()

    lock = BooleanField()
    complete = BooleanField()
    error = StringField()
    retry = IntField()

    def start(self):
        self.lock = True
        self.start_time = datetime.datetime.now()
        self.save()

    def stop(self):
        self.lock = False
        self.complete = True
        self.end_time = datetime.datetime.now()
        self.save()

    def set_error(self, error):
        self.error = str(error)
        self.save()
