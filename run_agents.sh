#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"

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

open_terminal "Inventory Agent (port 8080)" "uv run python -m src.agents.splunk_inventory_agent"
sleep 5

open_terminal "Query Agent (port 8082)" "uv run python -m src.agents.splunk_query_agent"
sleep 5

open_terminal "Jira Ticket Agent (port 8084)" "uv run python -m src.agents.jira_ticket_agent"
sleep 5

open_terminal "Routing Agent / Gradio UI (port 8083)" "uv run python -m src.agents.host_agent"
