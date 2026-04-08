from langchain_core.messages import HumanMessage, SystemMessage
from src.core.constants import HISTORY
from src.core.prompts import SYSTEM_PROMPT
from src.factory.agent_factory import get_agent
from src.interface.ai_service import AbstractAIService
from src.services.ai_utility import (
    clean_llm_output,
    get_conversational_rag_chain,
    update_history,
)


# Used as template: Template Method Design Pattern
class BaseAIService(AbstractAIService):
    def __init__(self) -> None:
        self.__messages = [SystemMessage(content=SYSTEM_PROMPT)]

    async def interact(self, user_message: str) -> tuple:
        agent = self._get_agent()
        self._append_user_query_to_messages(user_query=user_message)
        agent_response = await agent.ainvoke(self.__messages)
        ai_reply = agent_response.content
        return (
            ai_reply,
            self._get_token_cost(usage_metadata=agent_response.usage_metadata),
        )

    def chat(self, query: str, user_id: int) -> tuple:
        result = self._invoke_conv_rag_chain(query=query, user_id=user_id)
        cleaned_result = clean_llm_output(result.content)
        self._update_history(cleaned_result=cleaned_result, query=query)
        return cleaned_result, self._get_token_cost(
            usage_metadata=result.usage_metadata
        )

    def _update_history(self, cleaned_result: str, query: str):
        update_history(result=cleaned_result, query=query)

    def _invoke_conv_rag_chain(self, query: str, user_id: int):
        return get_conversational_rag_chain().invoke(
            {"question": query, "chat_history": HISTORY, "user_id": user_id}
        )

    def _get_token_cost(self, usage_metadata: dict | None):
        pass

    def _get_agent(self):
        return get_agent()

    def _append_user_query_to_messages(self, user_query: str):
        self.__messages.append(HumanMessage(user_query))
