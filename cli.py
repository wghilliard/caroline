"""
this is the command line interface to
- add tasks
    - to the database
    - to torque
- build a docker container? Dockerfile is ready!
"""

import os
import argparse
from models import Task
from mongoengine import connect
from config import MONGODB_DATABASE, INFLUX_IP, MONGODB_IP
import json
from utils import generate_c_id, check_dir
import subprocess as sp
import docker


def mk_pilot(data_volume_list, cmd_list, docker_image_name, queue=None, log_dir="/data/caroline/logs",
             username=None,
             influx_measurement=None, c_id=None, misc=None, docker_pull=False, nvidia_docker=False):
    """
    mk_pilot will create an object in the database with the meta data, create a script for torque,
    and submit the job to the torque queue.

    :param data_volume_list: list of mount points to bound as to the docker container, usually /data list(str())
    # :param namespace: something like docker_user NOTE: NO LEADING '/' str()
    :param cmd_list: list() if commands to be executed in the container list(str())
    :param docker_image_name: name of docker image container to run the command in str()
    :param queue: the torque queue to submit the job, if omitted Torque will decide str()
    :param log_dir: the directory inside the context of data_volume to command output to str()
    :param username: the username to be associated with the task str()
    :param influx_measurement: str()
    :param c_id: if you have a preset c_id you want to be used, else it will be generated str()
    :param misc: extra info in dictionary form to save to mongo and influx dict()
    :param docker_pull: should docker try to pull the latest image? bool()
    :param nvidia_docker: should the nvidia-docker wrapper be used? bool()
    :return: True if task was created and submitted, False if error bool()
    """

    # TODO phase out namespace from wrappers.

    task_object = Task()

    if c_id is None:
        task_object.c_id = generate_c_id()
    else:
        try:
            task_object.c_id = int(c_id)
        except Exception as e:
            print(e)
            print("INFO: int(c_id) failed")
            return False

    if misc is not None:
        task_object.misc = misc

    task_object.cmd_list = cmd_list
    task_object.log_file = os.path.abspath(
        os.path.join(log_dir, str(task_object.c_id) + ".caroline.log"))
    task_object.work_dir = "/opt"

    task_object.influx_measurement = influx_measurement

    if username:
        task_object.user = username

    task_object.save()

    for index, mount in enumerate(data_volume_list):
        # Ensure mount points are accessible...
        check_dir(mount)
        data_volume_list[index] = ("-v {0}:{0}".format(mount))

    data_volume = " ".join(data_volume_list)

    if nvidia_docker:
        docker_init_cmd = "nvidia-docker run {0} --name={3} --net=\"host\" -e MONGODB_IP={4} -e INFLUXDB_IP={5} {1} {2}".format(
            data_volume, docker_image_name, task_object.c_id,
            task_object.c_id, MONGODB_IP, INFLUX_IP)
    else:
        docker_init_cmd = "docker run {0} --name={3} --net=\"host\" -e MONGODB_IP={4} -e INFLUXDB_IP={5} {1} {2}".format(
            data_volume, docker_image_name, task_object.c_id,
            task_object.c_id, MONGODB_IP, INFLUX_IP)

    print("C_ID: `{0}`".format(task_object.c_id))
    print("Logging to ...\n    `{0}/{1}.torque.log`\n    `{0}/{1}.torque.err`".format(log_dir, str(task_object.c_id)))

    temp_file_path = os.path.join("/tmp", "{0}.run".format(task_object.c_id))

    print("Exec File: `{0}`".format(temp_file_path))

    with open(temp_file_path, "w+") as temp_file_handle:
        if queue is not None:
            print("#PBS -q {0}".format(queue), file=temp_file_handle)

        print("#PBS -o {0}/{1}.torque.log".format(log_dir, str(task_object.c_id)), file=temp_file_handle)
        print("#PBS -e {0}/{1}.torque.err".format(log_dir, str(task_object.c_id)), file=temp_file_handle)

        if docker_pull:
            print("docker pull {0}".format(docker_image_name), file=temp_file_handle)
        print(docker_init_cmd, file=temp_file_handle)

    try:
        sp.call("chmod +x {0} && qsub {0} && rm {0}".format(temp_file_path), shell=True)

    except Exception as e:
        print(e)
        return False

    return True


def cleanup():
    connect(MONGODB_DATABASE, host=MONGODB_IP)
    tasks = Task.objects()
    client = docker.from_env()

    for task in tasks:
        try:
            this = client.containers.get("{0}".format(task.c_id))
            this.remove(force=True)
            # sp.call("docker rm {0}".format(task.c_id))
        except Exception as e:
            print(e)

        try:
            sp.call("qdel {0}".format(task.pbs_job_id))
        except Exception as e:
            print(e)


if __name__ == '__main__':

    # ARG PARSE
    parser = argparse.ArgumentParser(description="CLI for caroline")
    parser.add_argument("--cmd", nargs="*", type=str, help="command to be executed in the container", default=None)
    parser.add_argument("-i", "--image", default=None, type=str,
                        help="name of docker image container to run the command in")
    parser.add_argument("-d", "--data", default=None, type=str,
                        help="mount point to the docker container, usually /data")
    parser.add_argument("-c", "--config", type=str, default="./config.json")
    parser.add_argument("-q", "--queue", type=str, default=None)

    connect(MONGODB_DATABASE, host=MONGODB_IP)
    args = parser.parse_args()
    config_data = dict()
    with open(args.config) as config_file_handle:
        config_data = json.load(config_file_handle)

    # setup parameters for mk_pilot()
    if args.image is None:
        docker_image_name = config_data['default_image']

    else:
        docker_image_name = args.image

    if args.data is None:
        data_volume_list = config_data['data_volume_list']
    else:
        data_volume_list = args.data

    if args.queue is None and config_data.get('queue'):
        queue = config_data['queue']
    else:
        queue = args.queue

    mk_pilot(data_volume_list, "docker_user", args.cmd[0], docker_image_name, queue,
             username=config_data.get('username'))
