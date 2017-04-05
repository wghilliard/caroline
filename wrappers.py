"""
a wrapper should be something that builds commands to be used with cli.mk_pilot
"""

from cli import mk_pilot
import shutil
import json
import os
from utils import mkdir_p, generate_c_id, link_jobs_by_c_id
from mongoengine import connect
from config import MONGODB_DATABASE, MONGODB_IP

import logging as lg


# import time

def looper(num_loops, tmp_output_dir, n_events):
    helper_list = list()
    # tmp_output_dir = "caroline_rc_4_test"
    for index in range(0, num_loops):
        tmp = lariatsoft_one("/data/docker_user/fcl_files/MC_geant4_pion-0.fcl",
                             "/data/docker_user/fcl_files/WireDump_3D.fcl",
                             tmp_output_dir, n_events, index)
        helper_list.append(tmp)

    # link_jobs_by_c_id(os.path.join("/data/docker_user", tmp_output_dir), helper_list, full_dest_path)
    #     TODO use helper_list to link files into new dirs?

    return helper_list


def lariatsoft_one(gen_fcl_file_path, conv_fcl_file_path, out_path, n_events, index, c_id=None):
    """
    lariatsoft_one represents the first iteration's generation and conversion steps
    Phases:
    1. Generate root files
    2. Convert with WireDump
    3. Convert to H5

    Workflow:
    1. copy a fickle file from a host directory to $DATA_VOLUME/docker_user/fcl_files
    2. build command
    3. execute mk_pilot

    make sure out_path is writeable!

    :param gen_fcl_file_path: a path on the host that ends with .fcl (used for generation phase) str()
    :param conv_fcl_file_path: a path on the host that ends with .fcl (used for conversion phase) str()
    :param out_path: a path with config_data.get('data_volume') as the root ex "$DATA_VOLUME/$NAMESPACE/electron/"
    :param n_events: integer number of events that should be generated (is this in total or per worker? probably per worker) int()
    :param index: single_gen_X where X is the index (batch_number?) int()
    :param c_id: the identifier that groups caroline executions together str()
    :return:
    """
    # python3 ./cli.py --cmd 'cp /data/docker_user/fcl_files/MC_geant4_pion-0.fcl
    # /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/MC_geant4_pion-0.fcl -n 5 -o /data/docker_user/single_gen_12.root'

    # ~~~~~DEV~~~~~~
    # # This won't work because c_id is used to retrieve jobs from the database. We need another way to inherit a
    # # previously defined unique identifier.
    # if c_id is None:
    #     c_id = generate_c_id()
    # else:
    #     try:
    #         c_id = str(c_id)
    #     except Exception as e:
    #         lg.exception(e)
    #         lg.error("You tried to use `{0}` as a c_id, however it is not a string... Try again pls...")
    #         return False
    # ~~~~~~~~~~~~~~~
    c_id = generate_c_id()

    gen_fcl_file_path = os.path.abspath(gen_fcl_file_path)
    conv_fcl_file_path = os.path.abspath(conv_fcl_file_path)

    config_data = dict()
    with open("./config.json") as config_file_handle:
        config_data = json.load(config_file_handle)

    data_volume = config_data.get('data_volume')
    volume_list = config_data.get('volumes')
    namespace = config_data.get('namespace')

    tmp_fcl_file_path = os.path.join(data_volume, namespace, "fcl_files/")

    try:
        shutil.copy(gen_fcl_file_path, tmp_fcl_file_path)
    except shutil.Error as e:
        lg.info(e)
        pass
    except Exception as e:
        lg.info(e)
        return False

    try:
        shutil.copy(conv_fcl_file_path, tmp_fcl_file_path)
    except shutil.Error as e:
        lg.info(e)
        pass
    except Exception as e:
        lg.info(e)
        return False

    # copy python? not for now (should use git instead)

    # make output directory?
    tmp_out_path = os.path.join(data_volume, namespace, out_path, str(c_id))
    try:
        mkdir_p(tmp_out_path)
    except Exception as e:
        lg.info(e)

    phase_one_output_path = os.path.join(tmp_out_path, "single_gen_{0}.root".format(index))
    gen_fcl_file_base = os.path.basename(gen_fcl_file_path)
    commands = list()
    # TODO use data_volume, namespace
    commands.append(
        "cp /data/docker_user/fcl_files/{0} /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/{0} -n {1} -o {2}".format(
            gen_fcl_file_base, n_events, phase_one_output_path))

    phase_two_output_path = os.path.join(tmp_out_path, "wire_dump_{0}.root".format(index))
    conv_fcl_file_base = os.path.basename(conv_fcl_file_path)
    # use data_volume, namespace,
    commands.append(
        "cp /data/docker_user/fcl_files/{0} /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/{0} -s {1} -T {2}".format(
            conv_fcl_file_base, phase_one_output_path, phase_two_output_path))
    #
    # # Assuming the python is there?
    # rick = os.path.join(tmp_out_path, "2D_h5")
    # morty = os.path.join(tmp_out_path, "3D_h5")
    #
    # commands.append(
    #     "source /opt/root/bin/thisroot.sh && python /opt/Wirecell_Root_Procssing/ProcessRootFile_WireCell.py {0} {1} {2}".format(
    #         phase_two_output_path, rick, morty))

    # TODO this is atrocious, please fix this (done)
    # command_final = " && ".join(commands)

    # TODO better queue assignment
    mk_pilot(volume_list, commands, config_data.get('default_image'), influx_measurement="lariatsoft_one",
             queue="cpu_queue", c_id=c_id)

    return c_id


def lariatsoft_two(in_path, conv_fcl_file_path, out_path):
    """
    lar_two should be used to convert root files to h5 using the new h5 method?
    :param in_path: path to the root file that should be convereted
    :param conv_fcl_file_path: path the to fickle file that will be used
    :param out_path: path that the file should be written to
    :return:
    """
    c_id = generate_c_id()

    config_data = dict()
    with open("./config.json") as config_file_handle:
        config_data = json.load(config_file_handle)

    volume_list = config_data.get('volumes')
    data_volume = config_data.get('data_volume')
    namespace = config_data.get('namespace')

    conv_fcl_file_path = os.path.abspath(conv_fcl_file_path)
    tmp_fcl_file_path = os.path.join(data_volume, namespace, "fcl_files/")

    try:
        shutil.copy(conv_fcl_file_path, tmp_fcl_file_path)
    except shutil.Error as e:
        lg.info(e)
        pass
    except Exception as e:
        lg.info(e)
        return False

    # copy python? not for now (should use git instead)


    tmp_out_path = os.path.join(data_volume, namespace, out_path, str(c_id))

    try:
        mkdir_p(tmp_out_path)
    except Exception as e:
        lg.info(e)

    phase_two_output_path = os.path.join(tmp_out_path,
                                         "wire_dump_{0}.root".format(in_path.replace(".root", "").split("_")[-1]))

    conv_fcl_file_base = os.path.basename(conv_fcl_file_path)

    commands = list()
    commands.append(
        "cp /data/docker_user/fcl_files/{0} /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/{0} -s {1} -T {2}".format(
            conv_fcl_file_base, in_path, phase_two_output_path))

    lg.info("pilot command: \n", commands)
    mk_pilot(volume_list, commands, config_data.get('default_image'), influx_measurement="lariatsoft_two",
             queue="cpu_queue", c_id=c_id)

    return True


def wire_cell(in_path, out_path, explicit=False):
    """

    :param in_path:
    :param out_path:
    :param explicit: is the in_path and out_path explicit or does it need to be generated? bool()
    :return:
    """
    c_id = generate_c_id()
    commands = list()

    config_data = dict()
    with open("./config.json") as config_file_handle:
        config_data = json.load(config_file_handle)

    data_volume = config_data.get('data_volume')
    namespace = config_data.get('namespace')

    if explicit:
        rick = os.path.join(out_path, "2D_h5")
        morty = os.path.join(out_path, "3D_h5")
    else:
        tmp_out_path = os.path.join(data_volume, namespace, out_path, str(c_id))

        rick = os.path.join(tmp_out_path, "2D_h5")
        morty = os.path.join(tmp_out_path, "3D_h5")

    commands.append(
        "source /opt/root/bin/thisroot.sh && python /opt/Wirecell_Root_Procssing/ProcessRootFile_WireCell.py {0} {1} {2}".format(
            in_path, rick, morty))

    lg.info("pilot command: \n", commands)
    if mk_pilot([data_volume], commands, "wghilliard/wire_cell:1.0", influx_measurement="wire_cell",
                queue="cpuqueue", c_id=c_id):

        return True

    else:
        return False


def dlkit():
    return


def p2n():
    return True


if __name__ == "__main__":
    connect(MONGODB_DATABASE, host=MONGODB_IP)
    # lariatsoft_one("/Users/wghilliard/one.fcl", "/Users/wghilliard/two.fcl", "10000", 5, 1)
    # lariatsoft_one("/data/docker_user/fcl_files/C_geant4_pion-0.fcl", "/data/docker_user/fcl_files/WireDump_3D.fcl", 10, 22)

    lariatsoft_one("/data/docker_user/fcl_files/MC_geant4_pion-0.fcl", "/data/docker_user/fcl_files/WireDump_3D.fcl",
                   "caroline_rc_2_test", 10, 22)

    # lariatsoft_two("/Users/wghilliard/single_gen_2.root", "/data/docker_user/fcl_files/WireDump_3D.fcl",
    #                "/data/docker_user/grayson_test_2")
    #
    # wire_cell("/data/docker_user/caroline_rc_test/1481095300/wire_dump_0.root",
    #           "/data/docker_user/caroline_rc_test/1481095300/")
