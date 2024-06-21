import logging
import json
from typing import List, Optional, Dict
from pydantic import BaseModel
from openai import OpenAI
from app.api.retrieval import get_law_context_chunks
from app.api.prompts import CHATBOT_PROMPT, RAG_PROMPT
from langchain_community.vectorstores.faiss import FAISS

logger = logging.getLogger(__name__)


class Message(BaseModel):
    content: str
    role: str


class Config(BaseModel):
    retrieve_n: int
    rerank_max_n: int
    max_context_len: int
    model: str
    client: OpenAI
    embedding_model: str
    db: FAISS
    use_reformulated_question: Optional[bool] = False

    class Config:
        arbitrary_types_allowed = True


############################################################################################
# ORIGINAL VERSION:
# enrich latest message with the additional context from RAG, and send all the mesage history
# to OpenAI before streaming response back to user
############################################################################################


def add_context_to_messages(messages, context):
    latest_message = messages[-1].content
    enriched_user_message = f"RAG context: {context}\n" f"Question to answer: {latest_message}\n"
    enriched_messages = messages[:-1] + [Message(content=enriched_user_message, role="user")]
    return enriched_messages


def process_chunk(chunk: bytes) -> str:
    content = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
    # Split the content into lines and prefix each with 'data: '
    # Then join them back together, ending with double newlines.
    return "\n".join("data: " + line for line in content.split("\n")) + "\n\n"


def get_openai_stream(messages: List[Message], config: Config):
    # Extract the configuration parameters
    client = config.client
    k = config.k
    max_context_len = config.max_context_len
    model = config.model
    embedding_model = config.embedding_model
    db = config.db

    print("Vector database type: ", type(db))
    # Retrieve the context relevant for the latest message and create the new message
    context = get_law_context_chunks(
        messages[-1].content,
        k=k,
        max_context_len=max_context_len,
        embedding_model=embedding_model,
        db=db,
    )[0]
    enriched_messages = add_context_to_messages(messages, context)

    # Prepend the messages with a system prompt
    enriched_messages = [Message(content=CHATBOT_PROMPT, role="system")] + enriched_messages

    # Get response from OpenAI
    logger.info("Sending API request to OpenAI")
    openai_stream = client.chat.completions.create(
        model=model, messages=enriched_messages, temperature=0, stream=True
    )
    for chunk in openai_stream:
        yield process_chunk(chunk)
    yield "data: [DONE]\n\n"  # Properly formatted SSE message for stream end if needed


############################################################################################
# NEW VERSION OF THE CHAT PROCESSING
# 1. Reformulate question (interpret what the user wants)
# 2. Search for relevant context
# 3. Send the system prompt, reformulated question, and the context to openAI
# 4. Stream back the response
############################################################################################
def reformulate_question(logged_messages: List[Message], config: Config):
    conversation_history = [message.model_dump() for message in logged_messages]
    # conversation_history = [message.dict() for message in logged_messages]
    conversation_history = [f"{msg['role']}: {msg['content']} \n" for msg in conversation_history]
    conversation_history_string = "".join(conversation_history)
    prompt = RAG_PROMPT.replace("{conversation_history}", conversation_history_string)
    message = [Message(role="user", content=prompt)]
    # logging.info(f"Reformulating question: {prompt}")
    completion = config.client.chat.completions.create(
        model="gpt-4o",
        messages=message,
        temperature=0,
        stream=False,
        response_format={"type": "json_object"},
    )
    response_json = json.loads(completion.choices[0].message.content)
    # logging.info(f"LLM reply to question reformulation: {response_json}")

    return response_json["reformulated_question"]


def process_text_for_sse_format(text: str) -> str:
    return "\n".join("data: " + line for line in text.split("\n")) + "\n\n"


def prettify_references(references: List[Dict]) -> str:
    if len(references) == 0:
        return ""

    markdown_references = "\n\nUporabljeni viri:\n"
    counter = 1
    for ref in references:
        new_reference_name = ref["details_href_name"]
        if new_reference_name not in markdown_references:
            new_reference = (
                f"* **[[{counter}]]({ref['raw_filepath']})** {ref['details_href_name']}\n"
            )
            counter += 1
            markdown_references += new_reference
    return markdown_references


def retrieve_context(
    messages: List[Message],
    reformulated_query,
    db,
    retrieve_n,
    rerank_max_n,
    max_context_len,
    embedding_model,
):
    # 1. Get the RAG context chunks
    law_context, law_context_references = get_law_context_chunks(
        reformulated_query,
        retrieve_n=retrieve_n,
        rerank_max_n=rerank_max_n,
        max_context_len=max_context_len,
        embedding_model=embedding_model,
        db=db,
    )

    # 2. Prepare the context chunk into a text, and references object
    markdown_references = prettify_references(law_context_references)

    # 3. Create the conversation history with references
    enriched_last_message = f"{messages[-1].content}\n\n{law_context}"
    messages_with_context = [
        Message(role="system", content=CHATBOT_PROMPT),
        *messages[:-1],
        Message(role="user", content=enriched_last_message),
    ]

    enriched_last_message = f"{reformulated_query}\n\n{law_context}"
    reformulated_message_with_context = [
        Message(role="system", content=CHATBOT_PROMPT),
        Message(role="user", content=enriched_last_message),
    ]

    return (
        messages_with_context,
        reformulated_message_with_context,
        markdown_references,
    )


def stream_response(enriched_messages, model, client):

    logger.info("Getting chatbot reply")
    openai_stream = client.chat.completions.create(
        model=model, messages=enriched_messages, temperature=0, stream=True
    )
    for chunk in openai_stream:
        yield process_chunk(chunk)

    yield "data: [DONE]\n\n"  # Properly formatted SSE message for stream end if needed


# Single API call to reformulate question, get refernces and send them to user, send the message to
# OpenAI and stream back the response to user
def process_question_and_stream_response(messages: List[Message], config: Config):

    # Extract the configuration parameters
    client = config.client
    retrieve_n = config.retrieve_n
    rerank_max_n = config.rerank_max_n
    max_context_len = config.max_context_len
    model = config.model
    db = config.db
    embedding_model = config.embedding_model
    db = config.db
    use_reformulated_question = config.use_reformulated_question
    logger.info("Extracted config properties")

    # Based on the logged messages, reformulate the latest user question
    reformulated_question = reformulate_question(messages, config)
    logging.info(f"Reformulated question: {reformulated_question}")
    # reformulated_question_into = "Search query:\n\n"
    # yield process_text_for_sse_format(reformulated_question_into + reformulated_question)

    # Retrieve the relevant references for the latest (reformulated) user question
    msg_hist_with_context, query_with_context, only_references = retrieve_context(
        messages,
        reformulated_question,
        db,
        retrieve_n,
        rerank_max_n,
        max_context_len,
        embedding_model,
    )
    if len(only_references) > 0:
        logging.info(f"Only references found: {only_references}")
        yield process_text_for_sse_format(only_references)

    # Send the (reformulated) question with the law excerpts to OpenAI and stream the response
    logger.info("Sending question to OpenAI")
    # answer_intro = "\n\n\n\nOdgovor:\n\n\n"
    # yield process_text_for_sse_format(answer_intro)
    empty_lines = "\n\n\n\n"
    yield process_text_for_sse_format(empty_lines)

    if use_reformulated_question:
        for chunk in stream_response(query_with_context, model, client):
            yield chunk
    else:
        for chunk in stream_response(msg_hist_with_context, model, client):
            yield chunk
    logger.info("Finished response")


if __name__ == "__main__":
    pass


############################################################################################
# What am I trying to accomplish? Being able to have a continuous conversation with the chatbot
# BACKEND
# 1. Reformulate question (interpret what the user wants)
# 2. Search for relevant context
# 3. Send the system prompt, reformulated question, and the context to openAI
# 4. Stream back the response

# FRONTEND:
# 1. Show loading sign while waiting for reformulated questions
# 2. Show the reformulated question
# 3. Receive the relevant references, and show them
# 4. Show the streaming response
