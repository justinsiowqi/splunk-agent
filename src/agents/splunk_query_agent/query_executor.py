import asyncio

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import UnsupportedOperationError
from .run import run_splunk_agent

class SplunkQueryAgentExecutor(AgentExecutor):
    def __init__(self, client, collection_id: str, chat_id: str):
        self.client = client
        self.collection_id = collection_id
        self.chat_id = chat_id

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            user_message = context.get_user_input()
            print(f"[execute] user_message={user_message!r}")
            response = await asyncio.to_thread(
                run_splunk_agent,
                client=self.client,
                chat_id=self.chat_id,
                user_prompt=user_message,
            )
            print(f"[execute] response={response!r}")
            await event_queue.enqueue_event(new_agent_text_message(response))
            print("[execute] event enqueued successfully")
        except Exception as e:
            print(f"[execute] ERROR: {type(e).__name__}: {e}")
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError()
