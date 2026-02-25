# Splunk & ngrok Setup Guide

Step-by-step instructions for setting up Splunk Enterprise locally and exposing it via ngrok. Once complete, return to the [README](README.md#quick-start) to configure and run the agents.

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

## 2. ngrok

ngrok creates a public HTTPS tunnel so H2OGPTE (in the cloud) can reach your local Splunk MCP server.

### Install

1. Create an account at [ngrok.com](https://ngrok.com)
2. Install and authenticate:

```bash
# macOS
brew install ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

For other platforms, see the [ngrok docs](https://ngrok.com/docs/getting-started/).

### Start the Tunnel

```bash
ngrok http https://localhost:8089
```

The displayed public URL (e.g. `https://abcd-1234.ngrok-free.app`) is your `SPLUNK_MCP_URL`.

### Verify

Open the ngrok URL in your browser to confirm it reaches Splunk.

---

Next: return to the [README](README.md#quick-start) to configure your `.env` file and start the agents.
