import langchain
import FAISS


def get_context(query, db, k=10, max_context_len=2048):
    # Get the top K results
    docs = db.similarity_search(query, k=k)
    law_articles_text = [doc.page_content for doc in docs]
    law_articles_sources = [doc.metadata for doc in docs]

    context = "Relevant law articles: \n "
    for article, source in zip(law_articles_text, law_articles_sources):
        if len(context) + len(f"{source}: {article}  #### \n") < max_context_len:
            context += f"{source}: {article}  #### \n"
    return context


if __name__ == "__main__":
    query = "Koliko je minimalna placa v Sloveniji?"
    # db = FAISS.load_local(os.path.join(ROOT_DIR, "data/vector_store", "gpt-4")
    # context = get_context(query, db)
