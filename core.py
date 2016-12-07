"""
Carline is designed to be a "pilot" program that will execute a monitor commands in a Docker container.

Workflow:
    1. establish database connection
    2. get meta data from task.json?
        2.1 dictionary -> meta DictField in object
    3. build and save object to database (locking)
    4. run task (wat does this mean? bash? python? how is it passed in?)
    5. clean up environment?
    6. update object in MongoDB
    7. add self to influx
"""

import argparse
import os
from config import MONGODB_DATABASE, MONGODB_IP
from mongoengine import connect
import subprocess as sp
from models import Task
from logging_utils import send_to_influx

# ARG PARSE
parser = argparse.ArgumentParser(description="caaarroollline")
parser.add_argument('-c', '--task-path', type=str, default='./task.json', help="path to task.json file")
parser.add_argument('c_id', type=str, help='an integer for the accumulator')


def main(c_id):
    # MONGODB
    try:
        connect(MONGODB_DATABASE, host=MONGODB_IP)
    except Exception as e:
        print(e)
        return

    task_object = Task.objects(c_id=c_id).first()
    if task_object is None:
        print("cannot find c_id {0} in {1}".format(c_id, MONGODB_DATABASE))
        return
    task_object.start()

    # TODO multiple separate commands?
    # for task in task_object.commands:
    #     run_task(task_object)

    if run_task(task_object):
        task_object.stop()
    else:
        # do something?
        pass

    if task_object.influx_measurement:
        send_to_influx(task_object)

    return


def run_task(task):
    try:
        if task.work_dir is not None:
            os.chdir(task.work_dir)
        with open(task.log_file, 'a+') as log_file_handle:

            for cmd in task.cmd_list:
                print(cmd, file=log_file_handle)
                task.set_status(cmd)
                sp.call(cmd, stderr=log_file_handle, stdout=log_file_handle, shell=True)

    except OSError as e:
        print(e)
        task.set_error(e)
        return False
    except Exception as e:
        print(e)
        task.set_error(e)
        return False

    return True


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.c_id)
