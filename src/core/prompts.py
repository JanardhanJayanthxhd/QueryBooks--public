from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = """
You are a helpful assistant, answer the question
carefully with precise answer.
"""

CONTEXTUALIZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                Given a chat history and the latest user question,
                reformulate the question to be standalone if it references
                the chat history (even several levels before).

                CRITICAL RULES:
                1.  OUTPUT MUST BE A QUESTION - never provide explanations or answers
                2.  If the question references "it", "that", "this", etc.,
                    replace with the actual subject from chat history
                3.  Keep the question concise - just add necessary context
                4.  If no context is needed or if the question is direct and
                    straight forward, then return the original question unchanged


                Examples:
                --- Specific questions ---
                - Input: "Explain it in more detail" (after discussing Chapter 8)
                - Output: "Explain Chapter 8 of Algorithms to Live By in more detail"

                - Input: "What's a story from that chapter?" (after discussing relaxation)
                - Output: "What's a story from the Relaxation chapter in Algorithms to Live By?"

                --- general questions ---
                - Input:  "what is the title of the book?"
                    (or any common query relevant to docs)
                - Process: understand it is not about the contents
                    from inside the book instead of the documents itself

                Remember: Only reformulate the QUESTION, never answer it.
            """,
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ]
)

QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Answer the question based on the following context:

            {context}

            Rules:
                -   Read the entire context before generating result
                -   If the question is any simple greeting or welcome
                    message then just reply with simple greeting,
                    If you cannot understand the question then ask doubts.
                -   If the question is out-of-context (meaning that the context
                    does not contain any relavant answer for question)
                    then reply that you do not have references to get answer.
                -   Only answer questions for which you have references to.
                -   Do not generate any additional symbols such as
                    slashes, \\n, \\t, or any other mark down symbols
            """,
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ]
)
