import os
import errno
import uuid
import subprocess as sp


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def generate_c_id():
    return str(uuid.uuid4())


def check_dir(directory_name):
    try:
        # TODO check the following...
        # os.path.exists(directory_name)
        sp.call("ls {0} > /dev/null".format(directory_name), shell=True)
        return True
    except Exception as e:
        print(e)
        return False


def link_jobs_by_c_id(prefix_path, c_id_list, dest_dir_path):
    for c_id in c_id_list:
        for item in os.listdir(os.path.join(prefix_path, c_id)):
            os.symlink(os.path.join(prefix_path, c_id, item), os.path.join(dest_dir_path, item))
    return True
