import asyncio
import os
import traceback

import gradio as gr

from .routing_agent import RoutingAgent
from dotenv import load_dotenv


load_dotenv(override=True)


async def main():
    """Main gradio app."""
    print('Initializing routing agent (connecting to remote A2A agents)...')
    routing_agent = await RoutingAgent.create(
        remote_agent_addresses=[
            os.getenv('SPLUNK_EXPLORER_AGENT_URL', 'http://localhost:8080'),
            os.getenv('SPLUNK_ANALYST_AGENT_URL', 'http://localhost:8082'),
            os.getenv('JIRA_ACTION_AGENT_URL', 'http://localhost:8084'),
        ]
    )

    if not routing_agent.remote_agent_connections:
        print(
            '\nERROR: No remote agents were discovered.\n'
            'Make sure the Splunk agents are running first:\n'
            '  python -m splunk_inventory_agent\n'
            '  python -m splunk_query_agent\n'
            'Then restart this host agent.\n'
        )
        return

    print(f'Connected to {len(routing_agent.remote_agent_connections)} agent(s): '
          f'{list(routing_agent.remote_agent_connections.keys())}')

    async def get_response_from_agent(
        message: str,
        history: list[gr.ChatMessage],
    ) -> str:
        """Get response from host agent."""
        try:
            response = await routing_agent.route(message)
            return response
        except Exception as e:
            print(f'Error in get_response_from_agent (Type: {type(e)}): {e}')
            traceback.print_exc()
            return 'An error occurred while processing your request. Please check the server logs for details.'

    with gr.Blocks(
        theme=gr.themes.Ocean(), title='A2A Host Agent'
    ) as demo:
        gr.ChatInterface(
            get_response_from_agent,
            title='A2A Host Agent',
            description='This assistant routes your queries to Explorer, Analyst, and Jira Action agents.',
        )

    print('Launching Gradio interface...')
    demo.queue().launch(
        server_name='0.0.0.0',
        server_port=8083,
    )
    print('Gradio application has been shut down.')


if __name__ == '__main__':
    asyncio.run(main())
