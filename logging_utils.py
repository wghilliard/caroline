from influxdb import InfluxDBClient
from config import INFLUX_DB


def send_to_influx(task, influxdb_ip, misc=None):
    client = InfluxDBClient(host=influxdb_ip, port=8086, database=INFLUX_DB)

    delta = task.end_time - task.start_time

    json_body = [
        {
            "measurement": str(task.influx_measurement),
            "tags": {
                "jobID": task.pk,
                "cID": task.c_id,
                "username": task.username

            },
            "time": str(task.start_time),
            "fields": {
                "jobDuration": float(delta.total_seconds()),
                "numCommands": len(task.cmd_list)

            }
        }
    ]

    if misc is not None and len(misc) > 0:
        for item in misc:
            json_body[0]['tags'][item] = misc[item]

    try:
        client.write_points(json_body)
        task.in_influx = True
        task.save()

    # create databse on 404?
    except Exception as e:
        print(e)
        return False

    return True


    # ============ DEAD CODE ============

    # if __name__ == "__main__":
    #     from config import INFLUX_IP
    #
    #     influx_client = InfluxDBClient(host=INFLUX_IP, database=INFLUX_DB)
    #     influx_client.create_database(INFLUX_DB)
    #     from models import Task
    #
    #     this = Task()

    # ===================================
