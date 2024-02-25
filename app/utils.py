from google.cloud import compute_v1
import os


def fetch_database_ip(internal=True):
    instance_name = os.environ["DATABASE_INSTANCE_NAME"]
    project = os.environ["PROJECT_ID"]
    zone = os.environ["DATABASE_INSTANCE_ZONE"]

    client = compute_v1.InstancesClient()
    instance = client.get(project=project, zone=zone, instance=instance_name)
    if internal:
        os.environ["DATABASE_IP_ADDRESS"] = instance.network_interfaces[0].network_i_p
    else:
        os.environ["DATABASE_IP_ADDRESS"] = instance.network_interfaces[0].access_configs[0].nat_i_p
