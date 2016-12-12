from mongoengine import connect
from wrappers import lariatsoft_one, wire_cell

if __name__ == "__main__":
    connect("caroline")
    for index in range(0, 10):
        lariatsoft_one("/data/docker_user/fcl_files/MC_geant4_pion-0.fcl",
                       "/data/docker_user/fcl_files/WireDump_3D.fcl", "caroline_rc_test", 10, index)
        # wirecell("caroline_rc_test
