from typing import List
from pydantic import BaseModel
from openai import OpenAI
from app.api.database_interface import get_topk_context_chunks
from typing import Optional
from langchain_community.vectorstores.faiss import FAISS


class Message(BaseModel):
    content: str
    role: str


class Config(BaseModel):
    k: int
    max_context_length: int
    model: str
    client: OpenAI
    embedding_model: str
    db: Optional[FAISS]

    class Config:
        arbitrary_types_allowed = True


def get_openai_stream(messages: List[Message], config: Config):
    # Extract the configuration parameters
    client = config.client
    k = config.k
    max_context_length = config.max_context_length
    model = config.model
    embedding_model = config.embedding_model
    db = config.db

    # Retrieve the context relevant for the latest message and create the new message
    context = get_topk_context_chunks(
        messages[-1].content,
        k=k,
        max_context_length=max_context_length,
        embedding_model=embedding_model,
        db=db,
    )
    enriched_messages = add_context_to_messages(messages, context)

    # Prepend the messages with a system prompt
    enriched_messages = [Message(content=add_system_prompt(), role="system")] + enriched_messages

    # Get response from OpenAI
    openai_stream = client.chat.completions.create(
        model=model, messages=enriched_messages, temperature=0, stream=True
    )
    for chunk in openai_stream:
        yield process_chunk(chunk)
    yield "data: [DONE]\n\n"  # Properly formatted SSE message for stream end if needed


def process_chunk(chunk: bytes) -> str:
    content = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
    # Split the content into lines and prefix each with 'data: '
    # Then join them back together, ending with double newlines.
    return "\n".join("data: " + line for line in content.split("\n")) + "\n\n"


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


def add_system_prompt():
    return """
You are taxGPT, a specialized assistant for Slovenian tax law inquiries.
Adhere to the following structured guidelines to ensure responses are comprehensive, accurate, and beneficial:

1. Contextual Information:
- You will receive context for each user query in the format provided by the Retrieval-Augmented Generation (RAG) pipeline,
which includes relevant Slovenian tax law excerpts. Each context chunk has the format as follows:

Source: {source_name}
Link: {url_link}
Text: {article}

You will have access to multiple such chunks. Utilize this provided information to answer user queries accurately.

2. Answering Protocol:
- Language: Communicate responses in clear, professional Slovenian.
- Tone: Maintain a formal and informative tone, suitable for licensed tax consultants.
- Structure:
    - Acknowledge the user's question with a brief introduction. List the facts provided by the user.
    - Based on the provided facts and the extracted law, think logically step by step and provide an informed answer.
    - Include a citation for each tax law reference, using the following format: "[{source_name}({url_link}})]"
    - DO NOT mention that for legal advice, users should consult a professional tax consultant. They are already aware of this.

3. User Engagement:
- There is no need to invite users to ask further questions or request clarifications.
- You must ask for more specific details if initial queries are broad or vague, to ensure relevant and comprehensive responses.
"""  # noqa: E501
