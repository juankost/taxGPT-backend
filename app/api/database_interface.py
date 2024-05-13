import tiktoken
import logging

logger = logging.getLogger(__name__)


def get_topk_context_chunks(
    query, k=10, max_context_length=4096, embedding_model="text-embedding-3-small", db=None
):
    """
    If it has access to the Vector DB locally, it tries to retrieve directly from DB,
    otherwise it calls the VM with the database
    """
    logger.info("Returning locally the context")
    return get_local_context(query, k, max_context_length, embedding_model, db)


def get_local_context(
    query, k=10, max_context_len=4096, embedding_model="text-embedding-3-small", db=None
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
        Source: {source["details_href_name"]}\n
        Link: {source["raw_filepath"]}\n
        Text: {article} \n
        """  # noqa: E501
        tokens = enc.encode(context + article_context)
        if len(tokens) < max_context_len:
            context += article_context
    return context
