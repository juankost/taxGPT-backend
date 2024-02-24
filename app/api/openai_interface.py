import openai
import os
from typing import List
from pydantic import BaseModel
from openai import OpenAI
from app.api.database_interface import get_topk_context_chunks

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()


class Message(BaseModel):
    content: str
    role: str


def get_openai_stream(messages: List[Message]):
    # Retrieve the context relevant for the latest message and create the new message
    latest_message = messages[-1].content
    context = get_topk_context_chunks(latest_message, k=10)
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


def add_context_to_message(message, context):
    return (
        f"{message} \n Here is some relevant context extracted from the law: {context} \n "
        f"To repeat, based on the information above, answer the question: {message}"
    )
