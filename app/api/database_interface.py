import requests
import os
import logging
from urllib.parse import urlunparse


def get_topk_context_chunks(query, k=10, max_context_length=4096):
    db_scheme = "http"  # Consider "https" for secure connections
    db_host = os.getenv("DATABASE_IP_ADDRESS")
    db_port = os.getenv("DATABASE_PORT")
    db_netloc = f"{db_host}:{db_port}"
    db_api_endpoint = urlunparse((db_scheme, db_netloc, "/get_context", "", "", ""))
    response = requests.post(db_api_endpoint, json={"query": query, "k": k, "max_context_length": max_context_length})
    if response.status_code == 200:
        context = response.json().get("context")
        return context
    else:
        logging.error("Error in response: ")
        return "Error in retrieving context from the database"
