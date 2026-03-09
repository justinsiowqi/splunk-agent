import asyncio
import os
import traceback

import gradio as gr

from .routing_agent import RoutingAgent
from dotenv import load_dotenv


load_dotenv(override=True)

CUSTOM_CSS = """
/* ── Global ── */
.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
    padding: 24px 48px !important;
}

/* ── Header banner ── */
#header-row {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a1025 40%, #2d1230 100%);
    border-radius: 12px;
    padding: 16px 28px;
    margin-bottom: 4px;
    border: 1px solid rgba(255, 128, 0, 0.2);
    box-shadow: 0 2px 16px rgba(255, 128, 0, 0.08);
    width: 100% !important;
    max-width: 100% !important;
}

#header-row .prose h1 {
    color: #ffffff !important;
    font-size: 1.5rem !important;
    margin-bottom: 0 !important;
    letter-spacing: -0.02em;
}
#header-row .prose p {
    color: #9ca3af !important;
    font-size: 0.85rem !important;
    margin: 0 !important;
}

/* ── Agent status pills (additional) ── */
#agent-pills {
    margin-bottom: 4px;
    min-height: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
}
.agent-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #1e1e2e;
    border: 1px solid #2d2d3d;
    border-radius: 24px;
    padding: 6px 16px;
    margin: 4px 6px;
    font-size: 0.85rem;
    color: #d1d5db;
    font-family: 'Inter', system-ui, sans-serif;
    transition: border-color 0.2s ease;
}
.agent-pill:hover {
    border-color: #ff8000;
}
.agent-pill .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
    flex-shrink: 0;
}
.agent-pill .agent-icon {
    font-size: 1rem;
}

/* ── User message bubble (dark theme) ── */
.user {
    background-color: #2a2a3e !important;
    color: #e5e7eb !important;
    border-color: #3d3d50 !important;
}
.user table, .user tr, .user td, .user th {
    border-color: #3d3d50 !important;
}

/* ── Chatbot container fixed width ── */
.wrapper {
    width: 100% !important;
    max-width: 100% !important;
    flex-grow: 1 !important;
}

/* ── Example suggestion buttons ── */
.examples .example {
    background: rgba(30, 30, 48, 0.85) !important;
    border: 1px solid #3d3d50 !important;
    border-radius: 12px !important;
    color: #d1d5db !important;
    padding: 12px 18px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}
.examples .example:hover {
    border-color: #ff8000 !important;
    background: rgba(37, 37, 56, 0.95) !important;
    color: #ffffff !important;
    box-shadow: 0 0 12px rgba(255, 128, 0, 0.15) !important;
}
.examples {
    gap: 10px !important;
}

/* ── Scrollbar (dark theme) ── */
* {
    scrollbar-color: #3d3d50 transparent;
    scrollbar-width: thin;
}
*::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
*::-webkit-scrollbar-track {
    background: transparent;
}
*::-webkit-scrollbar-thumb {
    background: #3d3d50;
    border-radius: 4px;
}
*::-webkit-scrollbar-thumb:hover {
    background: #4d4d60;
}

/* ── Footer ── */
#footer-row {
    margin-top: 4px;
}
#footer-row .prose {
    text-align: center;
    color: #6b7280 !important;
    font-size: 0.8rem !important;
}
"""


def _build_agent_pills_html(agent_names: list[str]) -> str:
    """Build HTML status pills with green online dots."""
    icon_map = {
        'inventory': '\U0001f50d',
        'query': '\U0001f4ca',
        'jira': '\U0001f3ab',
    }
    pills = []
    for name in agent_names:
        icon = next(
            (v for k, v in icon_map.items() if k in name.lower()),
            '\U0001f916',
        )
        pills.append(
            f'<span class="agent-pill">'
            f'<span class="status-dot"></span>'
            f'<span class="agent-icon">{icon}</span>'
            f'{name}'
            f'</span>'
        )
    return ''.join(pills)


SUGGESTION_QUERIES = [
    'What is the version of this Splunk instance?',
    'What indexes are available in Splunk?',
]


async def main():
    """Main gradio app."""
    print('Initializing routing agent (connecting to remote A2A agents)...')
    routing_agent = await RoutingAgent.create(
        remote_agent_addresses=[
            os.getenv('SPLUNK_INVENTORY_AGENT_URL', 'http://localhost:8080'),
            os.getenv('SPLUNK_QUERY_AGENT_URL', 'http://localhost:8082'),
            os.getenv('JIRA_TICKET_AGENT_URL', 'http://localhost:8084'),
        ]
    )

    if not routing_agent.remote_agent_connections:
        print(
            '\nERROR: No remote agents were discovered.\n'
            'Make sure the Splunk agents are running first.\n'
            'Then restart this host agent.\n'
        )
        return

    agent_names = list(routing_agent.remote_agent_connections.keys())
    print(f'Connected to {len(agent_names)} agent(s): {agent_names}')

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

    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.orange,
        secondary_hue=gr.themes.colors.stone,
        neutral_hue=gr.themes.colors.zinc,
        radius_size=gr.themes.sizes.radius_md,
        font=[
            gr.themes.GoogleFont('Inter'),
            'system-ui',
            'sans-serif',
        ],
    ).set(
        # Dark body
        body_background_fill='#0f0f1a',
        body_background_fill_dark='#0f0f1a',
        body_text_color='#e5e7eb',
        body_text_color_dark='#e5e7eb',
        body_text_color_subdued='#9ca3af',
        body_text_color_subdued_dark='#9ca3af',
        # Blocks / panels
        background_fill_primary='#1a1a2e',
        background_fill_primary_dark='#1a1a2e',
        background_fill_secondary='#161625',
        background_fill_secondary_dark='#161625',
        block_background_fill='#1a1a2e',
        block_background_fill_dark='#1a1a2e',
        block_border_color='#2d2d3d',
        block_border_color_dark='#2d2d3d',
        panel_background_fill='#161625',
        panel_background_fill_dark='#161625',
        panel_border_color='#2d2d3d',
        panel_border_color_dark='#2d2d3d',
        # Inputs
        input_background_fill='#1e1e30',
        input_background_fill_dark='#1e1e30',
        input_border_color='#3d3d50',
        input_border_color_dark='#3d3d50',
        input_border_color_focus='#ff8000',
        input_border_color_focus_dark='#ff8000',
        input_placeholder_color='#6b7280',
        input_placeholder_color_dark='#6b7280',
        # Primary buttons (Splunk orange)
        button_primary_background_fill='#ff8000',
        button_primary_background_fill_dark='#ff8000',
        button_primary_background_fill_hover='#e67300',
        button_primary_background_fill_hover_dark='#e67300',
        button_primary_text_color='#ffffff',
        button_primary_text_color_dark='#ffffff',
        # Secondary buttons
        button_secondary_background_fill='#1e1e30',
        button_secondary_background_fill_dark='#1e1e30',
        button_secondary_background_fill_hover='#2a2a3e',
        button_secondary_background_fill_hover_dark='#2a2a3e',
        button_secondary_border_color='#3d3d50',
        button_secondary_border_color_dark='#3d3d50',
        button_secondary_text_color='#d1d5db',
        button_secondary_text_color_dark='#d1d5db',
        # Borders / accents
        border_color_primary='#2d2d3d',
        border_color_primary_dark='#2d2d3d',
        border_color_accent='#ff8000',
        border_color_accent_dark='#ff8000',
        # User bubble
        color_accent_soft='#2a2a3e',
        color_accent_soft_dark='#2a2a3e',
        border_color_accent_subdued='#3d3d50',
        border_color_accent_subdued_dark='#3d3d50',
        # Code blocks
        code_background_fill='#161625',
        code_background_fill_dark='#161625',
    )

    with gr.Blocks(title='Splunk Security Assistant') as demo:
        # Header
        with gr.Row(elem_id='header-row'):
            gr.Markdown(
                '# \U0001f6e1\ufe0f Splunk Security Assistant\n'
                'Multi-agent system for security exploration, analysis, and ticket management.'
            )

        # Agent status pills
        with gr.Row(elem_id='agent-pills'):
            gr.HTML(_build_agent_pills_html(agent_names))

        # Chat interface with native example buttons
        chatbot = gr.Chatbot(
            height=520,
            placeholder='Ask me about your Splunk data \u2014 I\'ll route your query to the right agent.',
            elem_id='main-chatbot',
        )

        gr.ChatInterface(
            get_response_from_agent,
            chatbot=chatbot,
            examples=SUGGESTION_QUERIES,
        )

        # Footer
        with gr.Row(elem_id='footer-row'):
            gr.Markdown(
                f'Powered by A2A Protocol &nbsp;\u00b7&nbsp; {len(agent_names)} agents online'
            )

    print('Launching Gradio interface...')
    demo.queue().launch(
        server_name='0.0.0.0',
        server_port=8083,
        theme=theme,
        css=CUSTOM_CSS,
    )
    print('Gradio application has been shut down.')


if __name__ == '__main__':
    asyncio.run(main())
