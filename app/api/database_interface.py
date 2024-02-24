import requests
import os
from google.cloud import compute_v1
import logging


def fetch_database_ip():
    instance_name = os.environ["DATABASE_INSTANCE_NAME"]
    project = os.environ["PROJECT_ID"]
    zone = os.environ["DATABASE_INSTANCE_ZONE"]

    client = compute_v1.InstancesClient()
    instance = client.get(project=project, zone=zone, instance=instance_name)
    return instance.network_interfaces[0].network_i_p


def get_topk_context_chunks(query, k=10, max_context_length=4096):
    if os.getenv("DATABASE_IP_ADDRESS") is None:
        os.environ["DATABASE_IP_ADDRESS"] = fetch_database_ip()

    # TODO There must be a better way to do this

    # db_api_endpoint = "http://" + os.getenv("DATABASE_IP_ADDRESS") + ":" + os.getenv("DATABASE_PORT") + "/get_context"
    # response = requests.post(db_api_endpoint, json={"query": query, "k": k, "max_context_length": max_context_length})
    db_api_endpoint = "http://" + os.getenv("DATABASE_IP_ADDRESS") + ":" + os.getenv("DATABASE_PORT") + "/"
    logging.info(f"Sending request to {db_api_endpoint}")
    response = requests.get(db_api_endpoint)
    if response.status_code == 200:
        logging.info(f"Received response from {db_api_endpoint}")
        context = response.json().get("message")
        logging.info("Response: " + context)
        return context
    else:
        # Return error message
        return "Error in retrieving context from the database"
