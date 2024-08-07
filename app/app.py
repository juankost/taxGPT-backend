import os
import logging
import argparse
import uvicorn
import openai
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from dotenv import find_dotenv, load_dotenv
from app.api.openai_interface import (
    get_openai_stream,
    Config,
    Message,
    OpenAI,
    process_question_and_stream_response,
)

# from app.utils import fetch_database_ip
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from app.storage.storage_bucket import check_folder_exists, download_folder

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define the interfaces for the API calls
class UserQuery(BaseModel):
    query: str
    user_id: str
    chat_id: str
    session_id: str


class ChatRequest(BaseModel):
    messages: List[Message]
    previewToken: Optional[str] = None


# TODO: Only allow access from frontend domain, or from local development (how to do this)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.post("/api/chat_with_context")
async def stream_with_local_context(user_query: ChatRequest):
    logger.info("Chat with local context endpoint called")
    return StreamingResponse(
        get_openai_stream(user_query.messages, config),
        media_type="text/event-stream",
    )


@app.post("/api/chat")
async def chat(user_query: ChatRequest):
    logger.info("Chat endpoint called")
    return StreamingResponse(
        process_question_and_stream_response(user_query.messages, config),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--local", action="store_true", help="Run the server locally")
    args = args.parse_args()

    logger.info("Loading the environment variables")
    if args.local:
        load_dotenv(".env.local", override=True)
        # fetch_database_ip(internal=False)
    else:
        # All the environment variables are passed through one secret value --> Need to extract them
        environment_variables = os.environ.get("ENVIRONMENT_VARIABLES")
        with open(".env", "w") as f:
            f.write(environment_variables)
        load_dotenv(find_dotenv(), override=True)
        # fetch_database_ip(internal=True)

    # Load the Vector DB if we have access to
    logger.info("Loading the vector database")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH")
    STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME")
    if (
        STORAGE_BUCKET_NAME is not None
        and check_folder_exists(STORAGE_BUCKET_NAME, "vector_database", local=args.local)
        and not os.path.exists(os.path.join(VECTOR_DB_PATH, "index.faiss"))
    ):
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        download_folder(STORAGE_BUCKET_NAME, "vector_database", VECTOR_DB_PATH, local=args.local)

    # Initialize the vector store
    logger.info("Initializing the vector store")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    embedding_model = os.environ["EMBEDDING_MODEL"]
    embeddings = OpenAIEmbeddings(model=embedding_model)
    try:
        db = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print("Error loading the database", e)
        db = None

    # Initialize the config for the OpenAI interface
    config = Config(
        retrieve_n=int(os.environ.get("NUM_RETRIEVED_CHUNKS")),
        rerank_max_n=int(os.environ.get("NUM_RERANKED_CHUNKS")),
        max_context_len=int(os.environ.get("MAX_CONTEXT_LENGTH")),
        model=os.environ.get("GPT_MODEL"),
        client=OpenAI(api_key=os.environ.get("OPENAI_API_KEY")),
        embedding_model=embedding_model,
        db=db,
        use_reformulated_question=True,
    )

    # Start the Server
    port = int(
        os.environ.get("PORT", 8080)
    )  # Default to 8080 for local development, use PORT env var in Cloud Run
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
