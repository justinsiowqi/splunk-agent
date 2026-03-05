# Splunk & Cloudflared Setup Guide

Step-by-step instructions for setting up Splunk Enterprise locally and exposing it via cloudflared. Once complete, return to the [README](README.md#quick-start) to configure and run the agents.

## 1. Splunk Enterprise

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

```bash
export SPLUNK_HEC_TOKEN=<your_hec_token>
export SPLUNK_HEC_URL=https://localhost:8088/services/collector/event
python ingest.py mordor
```

To ingest a different dataset:

```bash
python ingest.py mordor --url <zip_url>
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

## 2. Cloudflared

Cloudflared creates public HTTPS tunnels so H2OGPTE (in the cloud) can reach your local Splunk MCP and Atlassian MCP servers. Unlike ngrok, cloudflared supports multiple simultaneous tunnels on the free tier.

### Install

```bash
# macOS
brew install cloudflared
```

For other platforms, see the [cloudflared docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

### Cloudflared Setup

1. Go to [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/) → **Networking** → **Tunnels** → **Create Tunnel**
2. Enter a tunnel name and select your operating system
3. Select **Run Terminal (Manual)** to get the run command with your token

### Start the Tunnels

Open two terminals:

```bash
# Terminal 1 — Splunk MCP (port 8089)
cloudflared tunnel --url https://localhost:8089

# Terminal 2 — Atlassian MCP (port 9000)
cloudflared tunnel --url http://localhost:9000
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
curl https://<splunk-tunnel>.trycloudflare.com/services/mcp

# Test Atlassian MCP
curl -X POST https://<jira-tunnel>.trycloudflare.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'
```

> **Note:** Quick tunnel URLs change every time you restart cloudflared. Update `.env` with the new URLs after each restart.

---

Next: return to the [README](README.md#quick-start) to configure your `.env` file and start the agents.
