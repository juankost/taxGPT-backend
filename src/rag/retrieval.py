import os

# from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
import tiktoken

_ = load_dotenv(find_dotenv())  # read local .env file


def get_context(query, db, k=10, max_context_len=4096):
    # Get the top K results
    enc = tiktoken.encoding_for_model("gpt-4")
    docs = db.similarity_search(query, k=k)
    law_articles_text = [doc.page_content for doc in docs]
    law_articles_sources = [doc.metadata for doc in docs]

    context = "Relevant law articles: \n "
    for article, source in zip(law_articles_text, law_articles_sources):
        tokens = enc.encode(context + f"{source['law']}: {article}  #### \n")
        if len(tokens) < max_context_len:
            context += f"{source['law']}: {article}  #### \n \n"
    return context


if __name__ == "__main__":
    ROOT_DIR = "/Users/juankostelec/Google_drive/Projects/taxGPT-backend"
    query = " kdo je davcni rezident Slovenije?"
    db = FAISS.load_local(os.path.join(ROOT_DIR, "data/vector_store/faiss_index_all_laws"), OpenAIEmbeddings())
    context = get_context(query, db)
    print(context)
