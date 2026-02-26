# Splunk Multi-Agent System

A multi-agent system that integrates [H2OGPTE](https://h2o.ai/platform/h2ogpte/) with Splunk via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) and the [Agent-to-Agent (A2A)](https://github.com/google/A2A) protocol. Users can query Splunk data using natural language through a Gradio UI, with requests routed to specialized agents.

## Architecture

```
YOUR MACHINE
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  User (Gradio UI)                    port 8083           │
│       │                                                  │
│       ▼                                                  │
│  Routing Agent (host_agent/)                             │
│       │ H2OGPTE LLM decides and orchestrates flow        │
│       ├───────────────┬───────────────┐                  │
│       │ A2A           │ A2A           │                  │
│       ▼               ▼               │                  │
│  Explorer Agent   Analyst Agent       │                  │
│  port 8080        port 8082           │                  │
│  (discovery)      (query execution)   │                  │
│       └───────────────┬───────────────┘                  │
│                       │ validated findings               │
│                       ▼                                  │
│                Jira Action Agent                         │
│                port 8084                                 │
│                (ticket actions)                          │
│                                                          │
│  Splunk Web UI                       port 8000           │
│  Splunk MCP Server                   port 8089           │
│       ▲                                                  │
│       │ ngrok tunnels this port                          │
└───────┼──────────────────────────────────────────────────┘
        │
        │ public HTTPS
        ▼
   ngrok URL  ──►  H2OGPTE (cloud)  ──►  MCP Tool Runner
```

**Explorer Agent** — Observes the Splunk environment without running heavy queries. Tools: `splunk_get_indexes`, `splunk_get_metadata`, `splunk_get_info`, `splunk_get_kv_store_collections`

**Analyst Agent** — Writes and executes SPL queries. Tools: `splunk_run_query`, `splunk_get_knowledge_objects`, `splunk_get_index_info`

**Jira Action Agent** — Creates and updates Jira tickets using validated findings from discovery and analysis.

## Prerequisites

- Python 3.9+
- Node.js with `npx` available in `PATH` (used by `mcp-remote`)
- An [H2OGPTE](https://h2o.ai/platform/h2ogpte/) instance with API access
- A running Splunk instance with the MCP Server app installed
- [ngrok](https://ngrok.com/) to expose Splunk MCP to H2OGPTE

> **First time?** See [SETUP.md](SETUP.md) for step-by-step instructions on setting up Splunk Enterprise and ngrok locally.

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/justinsiowqi/splunk-agent.git
cd splunk-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `H2OGPTE_API_KEY` | Your H2OGPTE API key |
| `H2OGPTE_ADDRESS` | H2OGPTE server URL (e.g. `https://your-instance.h2o.ai`) |
| `SPLUNK_HEC_URL` | URL pointing to Splunk HEC (port 8088) |
| `SPLUNK_HEC_TOKEN` | HEC token from Splunk app |
| `SPLUNK_MCP_URL` | ngrok public URL pointing to Splunk MCP (port 8089) |
| `SPLUNK_MCP_TOKEN` | Bearer token from Splunk MCP Server app |
| `SPLUNK_EXPLORER_AGENT_URL` | Explorer Agent URL (default: `http://localhost:8080`) |
| `SPLUNK_ANALYST_AGENT_URL` | Analyst Agent URL (default: `http://localhost:8082`) |
| `JIRA_MCP_URL` | Jira MCP endpoint URL |
| `JIRA_MCP_TOKEN` | Bearer token for Jira MCP |
| `JIRA_ACTION_AGENT_URL` | Jira Action Agent URL (default: `http://localhost:8084`) |

### 3. Start ngrok

```bash
ngrok http https://localhost:8089
```

Copy the public URL into `SPLUNK_MCP_URL` in your `.env` file.

### 4. Run the agents

Open four terminals:

```bash
# Terminal 1 — Explorer Agent (port 8080)
uv run python -m src.agents.splunk_explorer_agent

# Terminal 2 — Analyst Agent (port 8082)
uv run python -m src.agents.splunk_analyst_agent

# Terminal 3 — Jira Action Agent (port 8084)
uv run python -m src.agents.jira_action_agent

# Terminal 4 — Routing Agent with Gradio UI (port 8083)
uv run python -m src.agents.host_agent
```

Open http://localhost:8083 in your browser.

## Project Structure

```
splunk-agent/
├── src/
│   ├── agents/
│   │   ├── splunk_explorer_agent/     # Explorer Agent (environment discovery)
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── explorer_agent.py      # Agent Card definition
│   │   │   ├── explorer_executor.py   # A2A Agent Executor
│   │   │   ├── client.py              # H2OGPTE client initialization
│   │   │   ├── setup.py               # Collection, ingestion, and tool registration
│   │   │   └── query.py               # Chat session and LLM querying
│   │   ├── splunk_analyst_agent/      # Analyst Agent (query execution)
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── analyst_agent.py       # Agent Card definition
│   │   │   ├── analyst_executor.py    # A2A Agent Executor
│   │   │   ├── client.py              # H2OGPTE client initialization
│   │   │   ├── setup.py               # Collection, ingestion, and tool registration
│   │   │   └── query.py               # Chat session and LLM querying
│   │   ├── jira_action_agent/         # Jira Action Agent (ticket actions)
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── jira_action_agent.py   # Agent Card definition
│   │   │   ├── jira_action_executor.py # A2A Agent Executor
│   │   │   └── query.py               # Chat session and LLM querying
│   │   └── host_agent/                # Routing Agent (orchestrator + Gradio UI)
│   │       ├── __main__.py            # Gradio UI entry point
│   │       ├── routing_agent.py       # H2OGPTE-powered routing logic
│   │       └── remote_agent_connection.py # A2A client connections
│   ├── core/
│   │   ├── config.py                  # YAML config loader
│   │   └── prompt_loader.py           # System prompt loader
│   └── prompts/
│       ├── host_sys.md                # Routing agent system prompt
│       ├── explorer_sys.md            # Explorer agent system prompt
│       ├── analyst_sys.md             # Analyst agent system prompt
│       └── jira_action_sys.md         # Jira action agent system prompt
├── config/
│   └── agents.yaml                    # Agent configuration (LLM, tools, temperature)
├── mcp_config.json                    # Splunk MCP server configuration
├── mcp_config_jira.json               # Jira MCP server configuration
├── requirements.txt
├── .env.example
├── SETUP.md                           # Splunk & ngrok setup guide
└── README.md
```

## License

MIT
