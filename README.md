# H2O Splunk Agent

A Python agent that integrates [H2OGPTE](https://h2o.ai/platform/h2ogpte/) with Splunk via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling natural language queries against your Splunk instance using H2O's LLM platform.

## Overview

This project sets up an H2OGPTE multi-agent pipeline that:

1. Creates a document collection and ingests an MCP server configuration
2. Registers a remote Splunk MCP tool on the H2OGPTE platform
3. Configures secure agent keys for credential management
4. Enables natural language querying of Splunk data through an LLM agent

```
YOUR MACHINE
┌─────────────────────────────────────────────────────┐
│                                                     │
│  curl / other agent                                 │
│       │ HTTP POST                                   │
│       ▼                                             │
│  A2A Server (server.py)          port 8080          │
│       │ calls query_splunk_agent()                  │
│       │                                             │
│  Splunk web UI                   port 8000          │
│  Splunk MCP Server               port 8089          │
│       ▲                                             │
│       │ ngrok tunnels this port                     │
└───────┼─────────────────────────────────────────────┘
        │
        │ public HTTPS
        ▼
   ngrok.io URL  (the URL in mcp_config.json)
        │
        │ public HTTPS (outbound from H2OGPTE)
        ▼
┌─────────────────────────────────────────────────────┐
│  H2OGPTE  (H2O cloud)                               │
│                                                     │
│  LLM Agent  ──────►  MCP Tool Runner                │
│                           │                         │
│                           │ npx mcp-remote          │
│                           │ → ngrok URL             │
│                           │ → calls Splunk tools    │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- Node.js with `npx` available in `PATH` (used by `mcp-remote`)
- An H2OGPTE instance with API access
- A running Splunk MCP server accessible over HTTPS (e.g. exposed via [ngrok](https://ngrok.com/))

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-org/splunk-agent.git
cd splunk-agent
```

### 2. Create and activate a virtual environment: 
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment variables

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `H2OGPTE_API_KEY` | Your H2OGPTE API key |
| `H2OGPTE_ADDRESS` | H2OGPTE server URL (e.g. `https://your-instance.h2o.ai`) |
| `SPLUNK_MCP_TOKEN` | Bearer token for your Splunk MCP server |
| `A2A_HOST` | Default is localhost |
| `A2A_PORT` | Default is 8080 (avoid 8000 and 8089 for Splunk) |

## Usage

Run the A2A Server

```bash
python server.py
```

Run the Curl Command

```bash
splunk-agent % curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "msg-001",
        "role": "user",
        "parts": [{"kind": "text", "text": "Tell me the Splunk version."}]
      }
    }
  }'
```

## Project Structure

```
splunk-agent/
├── splunk_agent/
│   ├── __init__.py       # Public API exports
│   ├── client.py         # H2OGPTE client initialisation
│   ├── setup.py          # Collection, ingestion, and tool registration
│   ├── query.py          # Chat session and LLM querying
│   ├── agent.py          # Agent Card
│   └── agent_executor.py # Agent Exector Logic
├── main.py               # Entry point — runs full setup + sample query
├── server.py             # Start A2A Server
├── mcp_config.json       # Splunk MCP server configuration
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## License

MIT
