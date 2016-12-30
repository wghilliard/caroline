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
        sp.call("ls {0}".format(directory_name))
        return True
    except Exception as e:
        print(e)
        return False
