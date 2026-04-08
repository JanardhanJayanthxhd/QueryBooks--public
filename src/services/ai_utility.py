import re
from decimal import Decimal

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from src.core.constants import HISTORY, MODEL_COST_PER_MILLION_TOKENS
from src.core.log import logger
from src.core.prompts import CONTEXTUALIZE_PROMPT, QA_PROMPT
from src.factory.agent_factory import get_agent
from src.factory.vector_factory import get_vector_store


def update_history(result: str, query: str):
    """Appends the user's query and the AI's response to the global conversation history.

    This function is typically called after a successful LLM interaction to maintain
    the context for future turns in a conversational application.

    Args:
        result: The result object from the LLM call, expected to have a 'content' attribute (like an AIMessage).
        query: The user's input object, expected to have a 'query' attribute containing the question string.
    """
    HISTORY.append(HumanMessage(query))
    HISTORY.append(AIMessage(result))


def get_contextualize_rag_chain():
    """Constructs the chain responsible for rewriting a follow-up question into a standalone,
    contextualized question based on the chat history.

    This chain is a key component of the Conversational RAG pattern.

    Returns:
        A LangChain Runnable (LCEL chain) that takes chat history and the current question
        as input and outputs the reformulated questionstring.
    """
    logger.info("invoked contextualize rag")
    chain = CONTEXTUALIZE_PROMPT | get_agent() | StrOutputParser()
    return chain


def get_conversational_rag_chain():
    """Constructs the main Conversational Retrieval-Augmented Generation (RAG) chain.

    This chain orchestrates the entire RAG process: it retrieves contextualized documents,
    inserts them into the final QA prompt, and uses an LLM to generate the final answer.

    Returns:
        A LangChain Runnable (LCEL chain) that accepts a dictionary with 'question' and
        'chat_history' and returns the final AIMessage response.
    """
    logger.info("invoked conversational rag")
    chain = (
        {
            "context": RunnableLambda(contextualized_retrival) | format_docs,
            "question": lambda x: x["question"],
            "chat_history": lambda x: x.get("chat_history", []),
            "user_id": lambda x: x["user_id"],
        }
        | QA_PROMPT
        | get_agent()
    )
    return chain


def format_docs(docs: Document) -> str:
    """
    Parses retrieved documents into a structured string for LLM consumption.

    This function iterates through a list of LangChain Document objects,
    extracting both the page content and the source title from the metadata.
    By explicitly labeling the 'METADATA_TITLE', it helps the LLM distinguish
    between the actual book title and other titles mentioned within the text body.

    Args:
        docs (list[langchain_core.documents.Document]): A list of Document objects
            returned by a vector store similarity search.

    Returns:
        str: A single formatted string containing numbered documents with
            explicit metadata and content sections, separated by double newlines.
    """
    formatted_chunks = []
    for i, doc in enumerate(docs, start=1):
        doc_title = doc.metadata.get("title", "Unknown Title")
        doc_content = doc.page_content

        formatted_chunk = (
            f"--- DOCUMENT {i} ---\n"
            f"--- Metadata Title: {doc_title} ---\n"
            f"--- Document Content: {doc_content} ---\n"
        )
        formatted_chunks.append(formatted_chunk)

    return "\n\n".join(formatted_chunks)


def contextualized_retrival(input_dict) -> list[Document]:
    """Decides whether to retrieve documents using the original question or a reformulated question.

    If chat history is present, it calls the contextualization chain to generate a standalone
    question. It then uses the result to query the global retriever.

    Args:
        input_dict: A dictionary containing the current 'question' and 'chat_history'.

    Returns:
        A list of Document objects retrieved from the global RETRIEVER.
    """
    logger.info(f"context dict: {input_dict}")
    chat_history = input_dict.get("chat_history", [])
    logger.info(f"Chat history: {chat_history}")
    question = input_dict["question"]
    user_id = input_dict.get("user_id")
    logger.info(f"Looking for {user_id}'s documents")

    if chat_history:
        reformulated_question = get_contextualize_rag_chain().invoke(
            {"chat_history": chat_history, "question": question}
        )
        logger.info(f"Reformulated question: {reformulated_question}")
    else:
        reformulated_question = question
        logger.info(f"non reformulated question: {reformulated_question}")

    docs = get_vector_store().similarity_search(
        query=reformulated_question, k=10, filter={"user_id": user_id}
    )

    pretty_print_documents(docs=docs)
    return docs


def pretty_print_documents(docs: Document) -> None:
    """
    Pretty prints the page content of a list of LangChain Document objects.

    This function iterates through the list of Document objects, converts each
    document to its JSON representation, extracts the 'page_content', and then
    logs the cleaned content using the global logger.

    Args:
        docs: A list of LangChain Document objects to be printed.
              (Note: The function signature implies a single `Document`, but the
              implementation loops over it, suggesting it expects an iterable of `Document`.)

    Returns:
        None: The function logs the output and does not return a value.
    """
    for i, doc in enumerate(docs, 1):
        logger.info(
            f"DOC: {i}: {clean_llm_output(doc.to_json()['kwargs']['page_content'])}"
        )


def clean_llm_output(text: str) -> str:
    """Removes Markdown bold markers and cleans up all extraneous whitespace
    and special characters."""
    cleaned_text = re.sub(r"\*\*", "", text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    cleaned_text = cleaned_text.replace("*", "").replace("_", "").replace("\\", "")

    return cleaned_text


def calculate_token_cost(token_usage: dict, model_name: str) -> str:
    """Calculates the total monetary cost incurred for a given prompt-response pair based on token usage.

    The cost is calculated by summing the input token cost and the output token cost
    using the predefined cost rates for the specified model.

    Args:
        token_usage: A dictionary containing the token counts, expected to have keys "input_tokens" and "output_tokens".
        model_name: name of llm model (eg: gpt-4o-mini, gpt-5, etc..)

    Returns:
        A string representation of the total calculated cost (e.g., "0.00015").
    """
    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)
    return str(
        Decimal(
            get_input_token_cost(input_tokens=input_tokens, model_name=model_name)
            + get_output_token_cost(output_tokens=output_tokens, model_name=model_name)
        )
    )


def get_output_token_cost(output_tokens: int, model_name) -> float:
    """Calculates the monetary cost specifically for the output (response) tokens.

    The cost is based on the model's defined cost per million output tokens.

    Args:
        output_tokens: The number of tokens generated in the LLM's response.
        model_name: name of llm model (eg: gpt-4o-mini, gpt-5, etc..)

    Returns:
        The total cost of the output tokens as a float.
    """
    output_token_cost = output_tokens * (
        MODEL_COST_PER_MILLION_TOKENS[model_name]["o"] / 1_000_000
    )
    return output_token_cost


def get_input_token_cost(input_tokens: int, model_name: str) -> float:
    """Calculates the monetary cost specifically for the input (prompt/context) tokens.

    The cost is based on the model's defined cost per million input tokens.

    Args:
        input_tokens: The number of tokens sent to the LLM in the prompt and context.
        model_name: name of llm model (eg: gpt-4o-mini, gpt-5, etc..)

    Returns:
        The total cost of the input tokens as a float.
    """
    input_token_cost = input_tokens * (
        MODEL_COST_PER_MILLION_TOKENS[model_name]["i"] / 1_000_000
    )
    return input_token_cost
