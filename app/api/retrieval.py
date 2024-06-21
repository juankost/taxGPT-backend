import tiktoken
import logging
import cohere
import os

logger = logging.getLogger(__name__)


# Completely ballparked
MIN_EMBEDDING_SIMILARITY_SCORE = 0.5
MIN_RERANKING_SIMILARITY_SCORE = 0.5


def get_law_context_chunks(
    query,
    retrieve_n=25,
    rerank_max_n=5,
    max_context_len=4096,
    embedding_model="text-embedding-3-small",
    db=None,
):
    # First stage semantic retrieval
    enc = tiktoken.encoding_for_model(embedding_model)
    docs = db.similarity_search_with_score(query, k=retrieve_n)
    logging.info(f"Similarity scores of initial retrieval: {[score for _, score in docs]}")
    docs = [doc for doc, score in docs if float(score) > MIN_EMBEDDING_SIMILARITY_SCORE]
    law_articles_text = [doc.page_content for doc in docs]
    law_articles_sources = [doc.metadata for doc in docs]
    logging.info(f"Retrieved {len(law_articles_text)} law articles")

    # Reranking of the results and further filtering docs to less
    if len(law_articles_text) > rerank_max_n:
        co = cohere.Client(os.getenv("COHERE_API_KEY"))
        reranked_results = co.rerank(
            query=query,
            documents=law_articles_text,
            model="rerank-multilingual-v3.0",
            top_n=rerank_max_n,
            return_documents=False,
        )
        logging.info(
            f"Similarity scores of reranking: "
            f"{[item.relevance_score for item in reranked_results.results]}"
        )
        relevant_indeces = []
        for item in reranked_results.results:
            print(item)
            if float(item.relevance_score) > MIN_RERANKING_SIMILARITY_SCORE:
                relevant_indeces.append(item.index)
        law_articles_text = [law_articles_text[i] for i in relevant_indeces]
        law_articles_sources = [law_articles_sources[i] for i in relevant_indeces]

    logging.info(f"Reranked and filtered to {len(law_articles_text)} law articles")

    if len(law_articles_text) == 0:
        context = "No relevant law articles found"
        references = []
        return context, references

    references = []
    context = "Retrieved relevant context from the law: \n\n"
    for article, source in zip(law_articles_text, law_articles_sources):
        article_context = f"""
        Source: {source["details_href_name"]}\n
        Link: {source["raw_filepath"]}\n
        Text: {article} \n
        """  # noqa: E501
        tokens = enc.encode(context + article_context)
        if len(tokens) < max_context_len:
            context += article_context
            references.append(source)
    return context, references
