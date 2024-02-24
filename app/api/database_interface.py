import requests
import os


def get_topk_context_chunks(query, k=10, max_context_length=4096):
    db_api_endpoint = os.getenv("DATABASE_IP_ADDRESS") + "/get_context"
    response = requests.post(db_api_endpoint, json={"query": query, "k": k, "max_context_length": max_context_length})
    if response.status_code == 200:
        context = response.json().get("context")
        return context
    else:
        # Return error message
        return "Error in retrieving context from the database"
