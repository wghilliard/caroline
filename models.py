"""
This file contains models to be used as an ORM for the "caroline" database in MongoDB
"""

from mongoengine import Document, ListField, StringField, IntField, DictField, DateTimeField, BooleanField, LongField

import datetime


class Task(Document):
    meta = {'collection': 'tasks'}
    misc = DictField()
    username = StringField(default=None)
    name = StringField(default=None)
    influx_measurement = StringField(default=None)
    in_influx = BooleanField(default=False)

    pbs_job_id = StringField(default=None)

    c_id = StringField(required=True)
    command = StringField()
    cmd_list = ListField(StringField())

    log_file = StringField()
    work_dir = StringField(default=None)

    start_time = DateTimeField(default=None)
    end_time = DateTimeField(default=None)

    status = StringField(default=None)
    lock = BooleanField(default=False)
    complete = BooleanField(default=False)
    error = StringField(default=None)
    retry = IntField(default=0)

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

    def set_status(self, cmd):
        self.status = cmd
        self.save()
