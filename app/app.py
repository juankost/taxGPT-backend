import os
import logging
import argparse
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from dotenv import find_dotenv, load_dotenv
from app.api.openai_interface import get_openai_stream
from app.utils import fetch_database_ip

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# TODO: Only allow access from frontend domain, or from local development (how to do this)
app = FastAPI()
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


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.post("/api/chat_with_context")
async def stream(user_query: ChatRequest):
    logger.info("Chat with context endpoint called")
    return StreamingResponse(get_openai_stream(user_query.messages), media_type="text/event-stream")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--local", action="store_true", help="Run the server locally")
    args = args.parse_args()

    # Load environment variables
    if args.local:
        load_dotenv(".env.local", override=True)
        fetch_database_ip(internal=False)
    else:
        # All the environment variables are passed through one secret value --> Need to extract them
        environment_variables = os.environ.get("ENVIRONMENT_VARIABLES")
        with open(".env", "w") as f:
            f.write(environment_variables)
        load_dotenv(find_dotenv(), override=True)
        fetch_database_ip(internal=True)

    # Start the Server
    port = int(os.environ.get("PORT", 8080))  # Default to 8080 for local development, use PORT env var in Cloud Run
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
