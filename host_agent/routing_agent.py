import asyncio
import json
import os
import uuid

from typing import Any

import httpx

from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
)
from dotenv import load_dotenv
from h2ogpte import H2OGPTE
from .remote_agent_connection import (
    RemoteAgentConnections,
    TaskUpdateCallback,
)
from splunk_explorer_agent.client import create_client


load_dotenv()

DEFAULT_LLM = "openai/gpt-oss-120b"

ROUTING_SYSTEM_PROMPT = """You are a routing delegator. You decide which agent handles the user's request.

Available agents:
{agents}

Currently active agent: {active_agent}

ROUTING GUIDELINES:
- Use the Explorer Agent for questions about what data exists: listing indexes, checking metadata (hosts, sources, sourcetypes), getting Splunk instance info, or inspecting KV Store collections.
- Use the Analyst Agent for questions that require running SPL queries, retrieving search results, accessing knowledge objects (saved searches, alerts, macros), or getting detailed index configuration.
- If the user's intent is ambiguous, prefer the Explorer Agent first for discovery, then the Analyst Agent for deeper analysis.

You MUST respond with ONLY a JSON object in one of these exact formats:

To delegate: {{"action": "delegate", "agent_name": "<exact name from list above>", "task": "<what to ask the agent>"}}
To respond directly: {{"action": "respond", "message": "<your message>"}}

ALWAYS delegate to an agent when one is available. Do NOT try to answer questions yourself.
"""


def create_send_message_payload(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> dict[str, Any]:
    """Helper function to create the payload for sending a task."""
    payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': text}],
            'messageId': uuid.uuid4().hex,
        },
    }

    if task_id:
        payload['message']['taskId'] = task_id

    if context_id:
        payload['message']['contextId'] = context_id
    return payload


class RoutingAgent:
    """The Routing agent.

    This is the agent responsible for choosing which agents to send
    tasks to and coordinate their work. Uses H2OGPTE as the LLM brain
    to make routing decisions.
    """

    def __init__(
        self,
        h2ogpte_client: H2OGPTE,
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''
        # H2OGPTE client and session
        self.h2ogpte_client = h2ogpte_client
        self.chat_session_id: str | None = None
        # Instance-level state (replaces ADK context.state)
        self.session_id: str = str(uuid.uuid4())
        self.active_agent: str | None = None

    async def _async_init_components(
        self, remote_agent_addresses: list[str]
    ) -> None:
        """Asynchronous part of initialization."""
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try:
                    card = await card_resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(
                        f'ERROR: Failed to get agent card from {address}: {e}'
                    )
                except Exception as e:
                    print(
                        f'ERROR: Failed to initialize connection for {address}: {e}'
                    )

        # Build agent roster string
        agent_info = []
        for agent_detail_dict in self.list_remote_agents():
            agent_info.append(json.dumps(agent_detail_dict))
        self.agents = '\n'.join(agent_info)

        # Create H2OGPTE chat session for routing (no collection = pure LLM reasoning)
        self.chat_session_id = self.h2ogpte_client.create_chat_session(
            collection_id=None
        )
        print(f'Routing agent chat session created: {self.chat_session_id}')

    @classmethod
    async def create(
        cls,
        remote_agent_addresses: list[str],
        h2ogpte_client: H2OGPTE | None = None,
        task_callback: TaskUpdateCallback | None = None,
    ) -> 'RoutingAgent':
        """Create and asynchronously initialize an instance of the RoutingAgent."""
        if h2ogpte_client is None:
            h2ogpte_client = create_client()
        instance = cls(h2ogpte_client=h2ogpte_client, task_callback=task_callback)
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.cards:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            print(f'Found agent card: {card.model_dump(exclude_none=True)}')
            print('=' * 100)
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info

    async def route(self, user_message: str) -> str:
        """Route a user message to the appropriate remote agent via H2OGPTE LLM.

        Args:
            user_message: The user's natural language message.

        Returns:
            The response text from the remote agent, or a direct response.
        """
        # Build the system prompt with current agent roster and active agent
        system_prompt = ROUTING_SYSTEM_PROMPT.format(
            agents=self.agents,
            active_agent=self.active_agent or 'None',
        )

        # Call H2OGPTE LLM for routing decision (sync call wrapped in thread)
        def _query_llm():
            with self.h2ogpte_client.connect(self.chat_session_id) as session:
                reply = session.query(
                    message=user_message,
                    system_prompt=system_prompt,
                    llm=DEFAULT_LLM,
                    llm_args=dict(
                        response_format='json_object',
                        temperature=0,
                    ),
                )
            return reply.content

        llm_response = await asyncio.to_thread(_query_llm)
        print(f'Routing LLM response: {llm_response}')

        # Parse the routing decision
        try:
            decision = json.loads(llm_response)
        except json.JSONDecodeError:
            # LLM didn't return valid JSON — fall back to delegating the
            # original user message to the first available agent.
            return await self._fallback_delegate(user_message)

        action = decision.get('action')

        if action == 'respond':
            return decision.get('message', 'No response provided.')

        elif action == 'delegate':
            agent_name = decision.get('agent_name')
            task = decision.get('task')
            if not agent_name or not task:
                return await self._fallback_delegate(user_message)

            try:
                result = await self.send_message(agent_name, task)
                if result is None:
                    return f"Error: No response received from agent '{agent_name}'."
                return result
            except ValueError as e:
                return f'Error: {e}'
        else:
            # LLM returned JSON but didn't follow the format —
            # delegate the original user message to the first available agent.
            return await self._fallback_delegate(user_message)

    async def _fallback_delegate(self, user_message: str) -> str:
        """Delegate to the first available agent when LLM routing fails."""
        if not self.remote_agent_connections:
            return 'Error: No remote agents available.'
        agent_name = next(iter(self.remote_agent_connections))
        print(f'Fallback: delegating to {agent_name}')
        try:
            result = await self.send_message(agent_name, user_message)
            if result is None:
                return f"Error: No response received from agent '{agent_name}'."
            return result
        except ValueError as e:
            return f'Error: {e}'

    def _extract_response_text(self, task_result: Task) -> str:
        """Extract readable text from an A2A Task result."""
        if task_result.status and task_result.status.message:
            parts = task_result.status.message.parts
            if parts:
                texts = []
                for part in parts:
                    if part.type == 'text':
                        texts.append(part.text)
                    else:
                        texts.append(f'[{part.type} content]')
                return '\n'.join(texts)
        if task_result.artifacts:
            texts = []
            for artifact in task_result.artifacts:
                for part in artifact.parts:
                    if part.type == 'text':
                        texts.append(part.text)
            if texts:
                return '\n'.join(texts)
        return 'Agent completed task but returned no text content.'

    def _extract_message_text(self, message: Message) -> str:
        """Extract readable text from an A2A Message result."""
        if message.parts:
            texts = []
            for part in message.parts:
                if part.root.kind == 'text':
                    texts.append(part.root.text)
                else:
                    texts.append(f'[{part.root.kind} content]')
            return '\n'.join(texts)
        return 'Agent returned an empty message.'

    async def send_message(self, agent_name: str, task: str) -> str | None:
        """Sends a task to a remote agent via A2A protocol.

        Args:
            agent_name: The name of the agent to send the task to.
            task: The task description to send.

        Returns:
            The response text, or None on failure.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')

        self.active_agent = agent_name
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f'Client not available for {agent_name}')

        message_id = str(uuid.uuid4())

        payload = {
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': task}],
                'messageId': message_id,
            },
        }

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )
        send_response: SendMessageResponse = await client.send_message(
            message_request=message_request
        )
        print(
            'send_response',
            send_response.model_dump_json(exclude_none=True, indent=2),
        )

        if not isinstance(send_response.root, SendMessageSuccessResponse):
            print('received non-success response. Aborting get task')
            return None

        result = send_response.root.result

        # The server may return a Task or a Message depending on the executor.
        if isinstance(result, Task):
            return self._extract_response_text(result)
        elif isinstance(result, Message):
            return self._extract_message_text(result)
        else:
            print(f'unexpected result type: {type(result)}')
            return None


def get_routing_agent_sync() -> RoutingAgent:
    """Synchronously creates and initializes the RoutingAgent with H2OGPTE."""

    async def _async_main() -> RoutingAgent:
        return await RoutingAgent.create(
            remote_agent_addresses=[
                os.getenv('SPLUNK_EXPLORER_AGENT_URL', 'http://localhost:8080'),
                os.getenv('SPLUNK_ANALYST_AGENT_URL', 'http://localhost:8082')
            ]
        )

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if 'asyncio.run() cannot be called from a running event loop' in str(e):
            print(
                f'Warning: Could not initialize RoutingAgent with asyncio.run(): {e}. '
                'Consider initializing RoutingAgent within an async function.'
            )
        raise
