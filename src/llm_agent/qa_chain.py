import time
import threading
import logging
import numpy as np
from langchain.embeddings.openai import OpenAIEmbeddings  # noqa E402
from langchain.vectorstores import FAISS  # noqa E402


class Law:
    """
    A class that represents a law object.

    Attributes:
    -----------
    llm : object
        An object that represents a language model.
    law_index_path : str
        A string that represents the path to the law index.
    max_law_articles_considered : int
        An integer that represents the maximum number of law articles to consider.
    embeddings : object
        An object that represents the OpenAI embeddings.
    law_index : object
        An object that represents the FAISS index.
    logger : object
        An object that represents the logger.
    """

    def __init__(self, llm, law_index_path, max_law_articles_considered=40):
        """
        Constructs all the necessary attributes for the Law object.

        Parameters:
        -----------
            llm : object
                An object that represents a language model.
            law_index_path : str
                A string that represents the path to the law index.
            max_law_articles_considered : int
                An integer that represents the maximum number of law articles to consider.
        """
        self.embeddings = OpenAIEmbeddings()  # type: ignore
        self.law_index = FAISS.load_local(law_index_path, self.embeddings)
        self.max_law_articles_considered = max_law_articles_considered
        self.logger = logging.getLogger("Law")
        self.llm = llm

    def find_relevant_law_articles(self, question):
        """
        Finds the relevant law articles.

        Parameters:
        -----------
            question : str
                A string that represents the question.

        Returns:
        --------
            relevant_law_articles : list
                A list that represents the relevant law articles.
            sources : list
                A list that represents the sources.
        """
        docs = self.law_index.similarity_search(question, k=self.max_law_articles_considered)
        law_articles_text = [doc.page_content for doc in docs]
        law_articles_sources = [doc.metadata for doc in docs]
        return law_articles_text, law_articles_sources
