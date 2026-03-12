#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$DIR/.env"

open_terminal() {
  local title="$1"
  local cmd="$2"
  osascript <<EOF
tell application "Terminal"
  activate
  do script "echo '=== $title ===' && cd '$DIR' && source '$DIR/.venv/bin/activate' && set -a && source '$DIR/.env' && set +a && $cmd"
end tell
EOF
}

wait_for_port() {
  local name="$1"
  local port="$2"
  echo "Waiting for $name on port $port..."
  until nc -z localhost "$port" 2>/dev/null; do
    sleep 1
  done
  echo "$name is up."
}

extract_tunnel_url() {
  local log_file="$1"
  local timeout=30
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    url=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$log_file" 2>/dev/null | head -1)
    if [ -n "$url" ]; then
      echo "$url"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

update_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i '' "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
}

kill_port() {
  local port="$1"
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "Killing existing process(es) on port $port (PIDs: $pids)..."
    echo "$pids" | xargs kill 2>/dev/null
    sleep 1
  fi
}

# 0. Clean up ports
echo "Checking for existing processes on required ports..."
for port in 9000 8080 8082 8083 8084; do
  kill_port "$port"
done
echo ""

# 1. Start Splunk
echo "Starting Splunk..."
/Applications/Splunk/bin/splunk start
echo ""

# 2. Start Atlassian MCP
open_terminal "Atlassian MCP (port 9000)" "ENABLED_TOOLS=jira_create_issue uvx mcp-atlassian --transport streamable-http --port 9000 -vv"
wait_for_port "Atlassian MCP" 9000

# 3. Start cloudflared tunnels in background and capture URLs
SPLUNK_LOG=$(mktemp)
JIRA_LOG=$(mktemp)
trap "rm -f $SPLUNK_LOG $JIRA_LOG" EXIT

echo "Starting cloudflared tunnels..."
cloudflared tunnel --url https://localhost:8089 --no-tls-verify > "$SPLUNK_LOG" 2>&1 &
SPLUNK_CF_PID=$!

cloudflared tunnel --url http://localhost:9000 --no-tls-verify > "$JIRA_LOG" 2>&1 &
JIRA_CF_PID=$!

echo "Waiting for Splunk MCP tunnel URL..."
SPLUNK_TUNNEL_URL=$(extract_tunnel_url "$SPLUNK_LOG")
if [ -z "$SPLUNK_TUNNEL_URL" ]; then
  echo "ERROR: Could not detect Splunk tunnel URL within timeout."
  exit 1
fi
echo "Splunk MCP tunnel: $SPLUNK_TUNNEL_URL"

echo "Waiting for Atlassian MCP tunnel URL..."
JIRA_TUNNEL_URL=$(extract_tunnel_url "$JIRA_LOG")
if [ -z "$JIRA_TUNNEL_URL" ]; then
  echo "ERROR: Could not detect Atlassian tunnel URL within timeout."
  exit 1
fi
echo "Atlassian MCP tunnel: $JIRA_TUNNEL_URL"

# 4. Update .env with tunnel URLs
update_env "SPLUNK_MCP_URL" "${SPLUNK_TUNNEL_URL}/services/mcp"
update_env "JIRA_MCP_URL" "${JIRA_TUNNEL_URL}/mcp"
echo "Updated .env with tunnel URLs."
echo ""

# 5. Start agents
open_terminal "Inventory Agent (port 8080)" "uv run python -m src.agents.splunk_inventory_agent"
wait_for_port "Inventory Agent" 8080

open_terminal "Query Agent (port 8082)" "uv run python -m src.agents.splunk_query_agent"
wait_for_port "Query Agent" 8082

open_terminal "Jira Ticket Agent (port 8084)" "uv run python -m src.agents.jira_ticket_agent"
wait_for_port "Jira Ticket Agent" 8084

open_terminal "Routing Agent / Gradio UI (port 8083)" "uv run python -m src.agents.host_agent"

echo ""
echo "All services started. Open http://localhost:8083 in your browser."
echo "Cloudflared tunnels running in background (PIDs: $SPLUNK_CF_PID, $JIRA_CF_PID)."
echo "To stop tunnels: kill $SPLUNK_CF_PID $JIRA_CF_PID"

wait
