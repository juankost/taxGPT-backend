import os
import openai
import httpx
import json

import asyncio
from pydantic import BaseModel

# from typing import Generator, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from openai import OpenAI, AsyncOpenAI

from typing import List, Optional

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.rag.retrieval import get_context
from src.database.data_store import add_chat_history, get_chat_history, append_to_chat_history


ROOT_DIR = "/Users/juankostelec/Google_drive/Projects/taxGPT-backend"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()


app = FastAPI()

# TODO: This needs to be adapted for Production (i.e. only allow the frontend to access the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only; specify your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserQuery(BaseModel):
    query: str
    user_id: str
    chat_id: str
    session_id: str


class Message(BaseModel):
    content: str
    role: str


class ChatRequest(BaseModel):
    messages: List[Message]
    previewToken: Optional[str] = None


# Vector database for retrieving context
vector_db = FAISS.load_local(os.path.join(ROOT_DIR, "data/vector_store/faiss_index_all_laws"), OpenAIEmbeddings())


@app.get("/")
async def root():
    return {"message": "Hello World"}


def get_openai_stream(messages: List[Message]):
    # Retrieve the context relevant for the latest message and create the new message
    latest_message = messages[-1].content
    context = get_context(latest_message, vector_db, k=10, max_context_len=4096)
    enriched_user_message = add_context_to_message(latest_message, context)
    enriched_messages = messages[:-1] + [{"content": enriched_user_message, "role": "user"}]
    openai_stream = client.chat.completions.create(
        model="gpt-4-0125-preview", messages=enriched_messages, temperature=0, stream=True
    )
    for chunk in openai_stream:
        yield process_chunk(chunk)


def process_chunk(chunk: bytes) -> bytes:
    if chunk.choices[0].delta.content:
        return chunk.choices[0].delta.content
    else:
        return "\n"


@app.post("/api/rag_chat")
async def stream(user_query: ChatRequest):
    return StreamingResponse(get_openai_stream(user_query.messages), media_type="text/event-stream")


def add_context_to_message(message, context):
    return (
        f"{message} \n Here is some relevant context extracted from the law: {context} \n "
        f"To repeat, based on the information above, answer the question: {message}"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
