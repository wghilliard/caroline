from influxdb import InfluxDBClient
from config import INFLUX_DB, INFLUX_IP

influx_client = InfluxDBClient(host=INFLUX_IP, database=INFLUX_DB)


def send_to_influx(task):
    client = InfluxDBClient(host='localhost', port=8086, database=INFLUX_DB)

    delta = task.end_time - task.start_time

    # TODO add in extra json from output

    json_body = [
        {
            "measurement": str(task.influx_measurement),
            "tags": {
                "jobID": task.pk,
                "cID": task.c_id,
                # "fileName": os.path.basename(document.pcap_location),
                "username": task.username

            },
            "time": str(task.start_time),
            "fields": {
                "jobDuration": float(delta.total_seconds())
            }
        }
    ]

    client.write_points(json_body)

    return


if __name__ == "__main__":
    influx_client.create_database(INFLUX_DB)
    from models import Task

    this = Task()
