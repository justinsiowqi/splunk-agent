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
│       │ H2OGPTE LLM decides which agent to call          │
│       ├──────────────────────────┐                       │
│       │ A2A                      │ A2A                   │
│       ▼                          ▼                       │
│  Explorer Agent    Analyst Agent                         │
│  port 8080         port 8082                             │
│  (discovery)       (query execution)                     │
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
| `SPLUNK_INVENTORY_AGENT_URL` | Explorer Agent URL (default: `http://localhost:8080`) |
| `SPLUNK_QUERY_AGENT_URL` | Analyst Agent URL (default: `http://localhost:8082`) |

### 3. Start Splunk

```bash
/Applications/Splunk/bin/splunk start
```

### 4. Start ngrok

```bash
ngrok http https://localhost:8089
```

Copy the public URL into `SPLUNK_MCP_URL` in your `.env` file.

### 5. Run the agents

Open three terminals:

```bash
# Terminal 1 — Explorer Agent (port 8080)
uv run python -m src.agents.splunk_inventory_agent

# Terminal 2 — Analyst Agent (port 8082)
uv run python -m src.agents.splunk_query_agent

# Terminal 3 — Routing Agent with Gradio UI (port 8083)
uv run python -m src.agents.host_agent
```

Open http://localhost:8083 in your browser.

## Project Structure

```
splunk-agent/
├── src/
│   ├── agents/
│   │   ├── splunk_inventory_agent/    # Inventory Agent
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── inventory_agent.py     # Inventory agent card definition
│   │   │   ├── inventory_executor.py  # A2A Inventory Agent Executor
│   │   │   └── run.py                 # Chat session and LLM querying
│   │   ├── splunk_query_agent/        # Analyst Agent (query execution)
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── query_agent.py         # Query agent card definition
│   │   │   ├── query_executor.py      # A2A Query Agent Executor
│   │   │   └── run.py                 # Chat session and LLM querying
│   │   └── host_agent/                # Routing Agent (orchestrator + Gradio UI)
│   │       ├── __main__.py            # Gradio UI entry point
│   │       ├── routing_agent.py       # H2OGPTE-powered routing logic
│   │       └── remote_agent_connection.py # A2A client connections
│   ├── core/
│   │   ├── client.py                  # H2OGPTE client initialization
│   │   ├── config.py                  # YAML config loader
│   │   ├── prompt_loader.py           # System prompt loader
│   │   └── setup.py                   # Collection, ingestion, and tool registration
│   └── prompts/
│       ├── host_sys.md                # Routing agent system prompt
│       ├── explorer_sys.md            # Explorer agent system prompt
│       └── analyst_sys.md             # Analyst agent system prompt
├── config/
│   └── agents.yaml                    # Agent configuration (LLM, tools, temperature)
├── mcp_config.json                    # Splunk MCP server configuration
├── requirements.txt
├── .env.example
├── SETUP.md                           # Splunk & ngrok setup guide
└── README.md
```

## License

MIT
