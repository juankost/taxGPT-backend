import os
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from dotenv import find_dotenv, load_dotenv
from app.api.openai_interface import get_openai_stream

# Load environment variables from .env file
load_dotenv(find_dotenv())

# TODO: This needs to be adapted for Production (i.e. only allow the frontend to access the API)
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
    return {"message": "Hello World"}


@app.post("/api/chat_with_context")
async def stream(user_query: ChatRequest):
    return StreamingResponse(get_openai_stream(user_query.messages), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))  # Default to 8080 for local development, use PORT env var in Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
