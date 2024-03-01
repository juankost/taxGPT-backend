from typing import List
from pydantic import BaseModel
from openai import OpenAI
from app.api.database_interface import get_topk_context_chunks


class Message(BaseModel):
    content: str
    role: str


class Config(BaseModel):
    k: int
    max_context_length: int
    model: str
    client: OpenAI

    class Config:
        arbitrary_types_allowed = True


def get_openai_stream(messages: List[Message], config: Config):
    # Extract the configuration parameters
    client = config.client
    k = config.k
    max_context_length = config.max_context_length
    model = config.model

    # Retrieve the context relevant for the latest message and create the new message
    context = get_topk_context_chunks(messages[-1].content, k=k, max_context_length=max_context_length)
    enriched_messages = add_context_to_messages(messages, context)

    # Get response from OpenAI
    openai_stream = client.chat.completions.create(model=model, messages=enriched_messages, temperature=0, stream=True)
    for chunk in openai_stream:
        yield process_chunk(chunk)
    yield "[DONE]"


def process_chunk(chunk: bytes) -> bytes:
    if chunk.choices[0].delta.content:
        return chunk.choices[0].delta.content
    else:
        return "\n"


def add_context_to_messages(messages, context):
    latest_message = messages[-1].content
    enriched_user_message = (
        f"Question to answer: {latest_message}\n"
        f"{context}\n"
        f"To repeat, based on the information above, answer the question, and provide the sources used: {latest_message}\n"  # noqa: E501
        f"Answer: "
        "Sources used: "
    )
    enriched_messages = messages[:-1] + [Message(content=enriched_user_message, role="user")]
    return enriched_messages
