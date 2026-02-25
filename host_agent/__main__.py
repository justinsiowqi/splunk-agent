import sys
import traceback

import gradio as gr

from .routing_agent import get_routing_agent_sync

# Initialize at startup — the Splunk agent A2A server must be running already.
print('Initializing routing agent (connecting to remote A2A agents)...')
routing_agent = get_routing_agent_sync()

if not routing_agent.remote_agent_connections:
    print(
        '\nERROR: No remote agents were discovered.\n'
        'Make sure the Splunk agent is running first:  python server.py\n'
        'Then restart this host agent.\n'
    )
    sys.exit(1)

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


def main():
    """Main gradio app."""
    with gr.Blocks(
        theme=gr.themes.Ocean(), title='A2A Host Agent'
    ) as demo:
        gr.ChatInterface(
            get_response_from_agent,
            title='A2A Host Agent',
            description='This assistant routes your queries to specialized agents (e.g., Splunk).',
        )

    print('Launching Gradio interface...')
    demo.queue().launch(
        server_name='0.0.0.0',
        server_port=8083,
    )


if __name__ == '__main__':
    main()
