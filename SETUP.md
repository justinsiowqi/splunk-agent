# Splunk, Atlassian MCP & Cloudflared Setup Guide

Step-by-step instructions for setting up Splunk Enterprise, Atlassian MCP, and cloudflared tunnels locally. Once complete, return to the [README](README.md#quick-start) to configure and run the agents.

## 1. Splunk Enterprise MCP

> Documentation: [MCP Server for Splunk Platform](https://help.splunk.com/en/splunk-cloud-platform/mcp-server-for-splunk-platform/about-mcp-server-for-splunk-platform)

### Install and Start

1. Download [Splunk Enterprise](https://www.splunk.com/en_us/download/splunk-enterprise.html) and create an account
2. Start Splunk:

```bash
/Applications/Splunk/bin/splunk start
```

The web UI will be available at http://localhost:8000.

### Configure HTTP Event Collector (HEC)

1. Go to **Settings > Data Inputs**
2. Click **HTTP Event Collector** > **New Token**
   - Enter Name: `workshop`
   - Click **Next** > **Review** > **Submit**
3. Go to **Global Settings** and set **All Tokens: Enabled**
4. Copy the generated HEC token

### Create an Index

1. Go to **Settings > Indexes** > **New Index**
2. Enter Name: `mordor`
3. Click **Save**

### Ingest Data

The data scripts read `SPLUNK_HEC_TOKEN` and `SPLUNK_HEC_URL` from `.env` automatically. See [data/README.md](data/README.md) for full usage details.

Ingest the mordor dataset (default):

```bash
# Bulk ingest the  dataset
python data/ingest.py mordor

# Ingest at real-time with 10x speed
python data/replay.py mordor --speed 10
```

Or ingest your own dataset:

```bash
# Ingest a custom dataset
python data/ingest.py your_index --url https://example.com/dataset.zip
```

### Verify Ingested Data

1. Go to **Apps > Search & Reporting**
2. Run: `index="mordor"`

### Install Splunk MCP Server App

1. Go to **Apps > Find More Apps**
2. Search `MCP` and click **Install**
3. Enter your [splunk.com](https://splunk.com) credentials
4. Accept the License Agreement

### Enable API Token Access

1. Go to **Settings > Tokens** > **New Token**
2. Enter the user and audience
3. Click **Create** and copy the token — this is your `SPLUNK_MCP_TOKEN`

### Get the MCP Server Endpoint

1. Go to **Apps > Manage Apps** and find **Splunk MCP Server**
2. Click **Create Splunk MCP Encrypted Token** > **Create**
3. Copy the **MCP Server Endpoint** (typically `https://localhost:8089`)

### Verify Locally

```bash
curl -X POST https://localhost:8089/services/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer <your_SPLUNK_MCP_TOKEN>" \
  -k \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'

```

## 2. Atlassian MCP

The Atlassian MCP server exposes Jira as an MCP service so H2OGPTE can create and manage tickets.

> Documentation: [MCP Atlassian](https://mcp-atlassian.soomiles.com/docs)

### Create an API Token

1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**, enter a label, and click **Create**
3. Copy the generated token — this is your `JIRA_API_TOKEN`

### Authenticate

Set the following environment variables (or add them to your `.env`):

```bash
export JIRA_URL=https://your-instance.atlassian.net/
export JIRA_USERNAME=your-email@example.com
export JIRA_API_TOKEN=<your_api_token>
```

### Start the MCP Server

```bash
uvx mcp-atlassian --transport streamable-http --port 9000 -vv
```

### Verify Locally

```bash
curl -X POST http://localhost:9000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

## 3. Cloudflared

Cloudflared creates public HTTPS tunnels so H2OGPTE (in the cloud) can reach your local Splunk MCP and Atlassian MCP servers. 

### Install

```bash
# macOS
brew install cloudflared

# windows
winget install --id Cloudflare.cloudflared
```

For other platforms, see the [cloudflared docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

### Start the Tunnels

Open two terminals:

```bash
# Terminal 1 — Splunk MCP (port 8089)
cloudflared tunnel --url https://localhost:8089 --no-tls-verify

# Terminal 2 — Atlassian MCP (port 9000)
cloudflared tunnel --url http://localhost:9000 --no-tls-verify
```

Each tunnel prints a unique URL (e.g. `https://random-words.trycloudflare.com`).

### Update `.env`

Copy the tunnel URLs into your `.env` file, appending the MCP endpoint paths:

```
SPLUNK_MCP_URL=https://<splunk-tunnel>.trycloudflare.com/services/mcp
JIRA_MCP_URL=https://<jira-tunnel>.trycloudflare.com/mcp
```

### Verify

```bash
# Test Splunk MCP
curl -X POST https://<splunk-tunnel>.trycloudflare.com/services/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer <your_SPLUNK_MCP_TOKEN>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'


# Test Atlassian MCP
curl -X POST https://<jira-tunnel>.trycloudflare.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'

```

> **Note:** Quick tunnel URLs change every time you restart cloudflared. Update `.env` with the new URLs after each restart.

---

Next: return to the [README](README.md#quick-start) to run the agents.
