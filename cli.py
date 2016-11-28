"""
this is the command line interface to
- add tasks
    - to the database
    - to torque
- build a docker container?
"""

import os
import argparse
from models import Task
from mongoengine import connect
from config import MONGODB_DATABASE
import json
import time
import subprocess as sp

# ARG PARSE
parser = argparse.ArgumentParser(description="CLI for caroline")
parser.add_argument("--cmd", nargs="*", type=str, help="command to be executed in the container", default=None)
parser.add_argument("-i", "--image", default=None, type=str,
                    help="name of docker image container to run the command in")
parser.add_argument("-d", "--data", default=None, type=str,
                    help="mount point to bound as /data to the docker container, usually /data")
parser.add_argument("-c", "--config", type=str, default="./config.json")
parser.add_argument("-q", "--queue", type=str, default=None)


def mk_pilot(data_volume, command, docker_image_name, queue=None, username=None):
    """
    Main will create an object in the database with the meta data, create a script for torque,
    and submit the job to the torque queue.

    :param data_volume: mount point to bound as /data to the docker container, usually /data
    :param command: command to be executed in the container
    :param docker_image_name: name of docker image container to run the command in
    :param queue: the torque queue to submit the job, if ommitted Torque will decide
    :param username: the username to be associated with the task
    :return: True if task was created and submitted, False if error
    """

    task_object = Task()
    task_object.c_id = int(time.time())
    task_object.command = command
    task_object.log_file = os.path.abspath(
        os.path.join(data_volume, config_data['log_dir'], str(task_object.c_id) + ".log"))
    task_object.work_dir = "/opt"
    if username:
        task_object.user = username

    task_object.save()

    docker_init_cmd = "docker run -itv {0}:/data --net=\"host\"{1} python3 /opt/caroline/core.py {2}".format(data_volume,
                                                                                                docker_image_name,
                                                                                                task_object.c_id)

    temp_file_path = os.path.join("/tmp", "{0}.run".format(task_object.c_id))

    print("writing exec file to: `{0}`".format(temp_file_path))

    with open(temp_file_path, "w+") as temp_file_handle:
        if queue is not None:
            print("#PBS -q {0}".format(queue), file=temp_file_handle)
        print(docker_init_cmd, file=temp_file_handle)

    try:
        sp.call("chmod +x {0} && qsub {0} && rm {0}".format(temp_file_path), shell=True)

    except Exception as e:
        print(e)
        return False

    return True


if __name__ == '__main__':

    # init
    connect(MONGODB_DATABASE)
    args = parser.parse_args()
    config_data = dict()
    with open(args.config) as config_file_handle:
        config_data = json.load(config_file_handle)

    # setup parameters for main()
    if args.image is None:
        docker_image_name = config_data['default_image']

    else:
        docker_image_name = args.image

    if args.data is None:
        data_volume = config_data['data_volume']
    else:
        data_volume = args.data

    if args.queue is None and config_data.get('queue'):
        queue = config_data['queue']
    else:
        queue = args.queue

    mk_pilot(data_volume, args.cmd[0], docker_image_name, queue, username=config_data.get('username'))
