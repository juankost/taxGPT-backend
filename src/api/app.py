import os
import openai

# import asyncio
from pydantic import BaseModel
from typing import Generator, AsyncGenerator
from fastapi import FastAPI

from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings  # noqa E402

from src.rag.retrieval import get_context


ROOT_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()


class UserQuery(BaseModel):
    query: str
    session_id: int


# Placeholder for the database containing the conversation histories
# This will be replaced with a database connection
# For now, we will use a dictionary
conversation_histories = {}


# Vector database for retrieving context
vector_db = FAISS.load_local(os.path.join(ROOT_DIR, "data/vector_store/faiss_index_all_laws"), OpenAIEmbeddings())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/chat")
async def chat(user_query: UserQuery):
    session_id = user_query.session_id
    user_message = user_query.query

    # Retrieve or initialize the conversation history for the given session_id
    conversation = conversation_histories.get(session_id, [])
    enriched_conversation = conversation.copy()

    # Retrieve the context relevant for the latest message
    context = get_context(user_message, vector_db, k=10, max_context_len=4096)

    # Create new message for the API:
    enriched_user_message = add_context_to_message(user_message, context)

    # Add the new user message to the conversation history
    enriched_conversation.append({"role": "user", "content": enriched_user_message})  # to pass to LLM
    conversation.copy().append({"role": "user", "content": user_message})  # for logging

    # Send the entire conversation history to OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4-0125-preview", messages=enriched_conversation, temperature=0, stream=False
    )

    # Add the OpenAI response to the conversation history
    conversation.append({"role": "assistant", "content": response.choices[0].message["content"]})

    # Save the updated conversation history
    conversation_histories[session_id] = conversation

    return {"response": response.choices[0].message["content"]}


def add_context_to_message(message, context):
    return (
        f"{message} \n Here is some relevant context extracted from the law: {context} \n To repeat, based on the "
        "information above, answer the question: {message}"
    )


# Why am I doing this?
# 1. Learning the building blocks that are needed to create and app: database, api, language model, node.js, etc.
# 2. Have a demo to show people of what I've done


# NEXT STEPS:
# Test chat history
# Connect databae to keep track of the chat histories
# Test with the database connection
# How can I deploy the API to production? Vercel???

# Frontend let's restart from the template
#


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
