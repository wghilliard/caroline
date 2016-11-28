"""
wrappers should be something that builds commands to be used with cli.mk_pilot
"""

from cli import mk_pilot
import shutil
import json
import os
from utils import mkdir_p


def lariatsoft_one(gen_fcl_file_path, conv_fcl_file_path, out_path, n_events, index):
    """
    lariatsoft_one represents the first iteration's generation and conversion steps
    Phases:
    1. Generate
    2. Convert with WireDump
    3. Convert to H5

    Workflow:
    1. copy a fickle file from a host directory to $DATA_VOLUME/docker_user/fcl_files
    2. build command
    3. execute mk_pilot
    :param gen_fcl_file_path: a path on the host that ends with .fcl (used for generation phase)
    :param conv_fcl_file_path: a path on the host that ends with .fcl (used for conversion phase)
    :param out_path: a path with config_data.get('data_volume') as the root ex "$DATA_VOLUME/docker_user/electron/"
    :param n_events: integer number of events that should be generated
    :param index: single_gen_X where X is the index
    :return:
    """
    # python3 ./cli.py --cmd 'cp /data/docker_user/fcl_files/MC_geant4_pion-0.fcl
    # /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/MC_geant4_pion-0.fcl -n 5 -o /data/docker_user/single_gen_12.root'

    gen_fcl_file_path = os.path.abspath(gen_fcl_file_path)
    conv_fcl_file_path = os.path.abspath(conv_fcl_file_path)

    config_data = dict()
    with open("./config.json") as config_file_handle:
        config_data = json.load(config_file_handle)

    data_volume = config_data.get('data_volume')

    tmp_fcl_file_path = os.path.join(data_volume, "docker_user/fcl_files")
    try:
        shutil.copy(gen_fcl_file_path, tmp_fcl_file_path)
    except shutil.Error as e:
        print(e)
        pass
    except Exception as e:
        print(e)
        return False

    try:
        shutil.copy(conv_fcl_file_path, tmp_fcl_file_path)
    except shutil.Error as e:
        print(e)
        pass
    except Exception as e:
        print(e)
        return False

    # copy python? not for now (should use git instead)
    try:
        mkdir_p(os.path.join(data_volume, out_path))
    except Exception as e:
        print(e)

    phase_one_output_path = os.path.join(data_volume, out_path, "single_gen_{0}.root".format(index))
    gen_fcl_file_base = os.path.basename(gen_fcl_file_path)
    commands = list()
    commands.append(
        "cp /data/docker_user/fcl_files/{0} /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/{0} -n {1} -o {2}".format(
            gen_fcl_file_base, n_events, phase_one_output_path))

    phase_two_output_path = os.path.join(data_volume, out_path, "wire_dump_{0}.root".format(index))
    conv_fcl_file_base = os.path.basename(conv_fcl_file_path)
    commands.append(
        "cp /data/docker_user/fcl_files/{0} /products/dev && source /etc/lariatsoft_setup.sh && lar -c /products/dev/{0} -s {1} -T {2}".format(
            conv_fcl_file_base, phase_one_output_path, phase_two_output_path))

    # Assuming the python is there?
    fuck = os.path.join(data_volume, out_path, "2D_h5")
    this = os.path.join(data_volume, out_path, "3D_h5")

    commands.append("python /opt/Wirecell_Root_Procssing/ProcessRootFile_WireCell.py {0} {1}".format(
        phase_two_output_path, fuck, this))

    # TODO this is atrocious, please fix this
    command_final = " && ".join(commands)

    print(command_final)
    mk_pilot(data_volume, command_final, config_data.get('default_image'))

    return True


if __name__ == "__main__":
    lariatsoft_one("/Users/wghilliard/one.fcl", "/Users/wghilliard/two.fcl", "docker_user/10000", 5, 1)
