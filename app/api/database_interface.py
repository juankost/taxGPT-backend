import requests
import tiktoken
import logging
import os
from urllib.parse import urlunparse


def get_topk_context_chunks(
    query, k=10, max_context_length=4096, embedding_model="text-embedding-3-small", db=None
):
    """
    If it has access to the Vector DB locally, it tries to retrieve directly from DB,
    otherwise it calls the VM with the database
    """
    if db is not None:
        return get_local_context(query, db, k, max_context_length, embedding_model)
    else:
        db_scheme = "http"  # Consider "https" for secure connections
        db_host = os.getenv("DATABASE_IP_ADDRESS")
        db_port = os.getenv("DATABASE_PORT")
        db_netloc = f"{db_host}:{db_port}"
        db_api_endpoint = urlunparse((db_scheme, db_netloc, "/get_context", "", "", ""))
        response = requests.post(
            db_api_endpoint,
            json={
                "query": query,
                "k": k,
                "max_context_length": max_context_length,
                "embedding_model": embedding_model,
            },
        )
        if response.status_code == 200:
            context = response.json().get("context")
            return context
        else:
            logging.error("Error in response: ")
            return "Error in retrieving context from the database"


def get_local_context(
    query, db, k=10, max_context_len=4096, embedding_model="text-embedding-3-small"
):
    # Get the top K results
    enc = tiktoken.encoding_for_model(embedding_model)
    docs = db.similarity_search(query, k=k)
    law_articles_text = [doc.page_content for doc in docs]
    law_articles_sources = [doc.metadata for doc in docs]

    logging.info(f"Retrieved {len(law_articles_text)} law articles")

    context = "Here is some relevant context extracted from the law: \n\n"
    for article, source in zip(law_articles_text, law_articles_sources):
        article_context = f"""
        Source: {source["filename"]}\n
        Link: {source["raw_filepath"]}\n
        Text: {article} \n
        """  # noqa: E501
        tokens = enc.encode(context + article_context)
        if len(tokens) < max_context_len:
            context += article_context
    return context
