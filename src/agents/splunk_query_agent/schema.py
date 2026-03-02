import json
import os

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _splunk_rest(endpoint: str, method: str = "GET", **params) -> requests.Response:
    """Call a Splunk REST API endpoint with basic auth.

    Args:
        endpoint: The REST path, e.g. "/services/data/indexes".
        method: HTTP method (GET or POST).
        **params: Extra query/form params forwarded to the request.

    Returns:
        The HTTP response object.
    """
    host = os.environ.get("SPLUNK_HOST", "localhost")
    port = os.environ.get("SPLUNK_MGMT_PORT", "8089")
    username = os.environ.get("SPLUNK_USERNAME", "admin")
    password = os.environ.get("SPLUNK_PASSWORD", "")

    url = f"https://{host}:{port}{endpoint}"
    auth = (username, password)

    params["output_mode"] = "json"

    if method.upper() == "GET":
        return requests.get(url, params=params, auth=auth, verify=False)
    return requests.post(url, data=params, auth=auth, verify=False)


def get_dynamic_schema(days_back: int = 30) -> str:
    """Discover active Splunk indexes and their key fields via REST API.

    Calls the Splunk management API directly to enumerate non-internal
    indexes, then runs a fieldsummary SPL query per index to discover
    the top fields.

    Args:
        days_back: How far back to look for active data.

    Returns:
        A markdown string describing the discovered schema.
    """
    # 1. List all indexes
    resp = _splunk_rest("/services/data/indexes")
    resp.raise_for_status()
    entries = resp.json().get("entry", [])

    # Filter to non-internal indexes with data
    indexes = []
    for entry in entries:
        name = entry["name"]
        if name.startswith("_"):
            continue
        event_count = int(entry.get("content", {}).get("totalEventCount", "0"))
        if event_count == 0:
            continue
        indexes.append({
            "name": name,
            "total_event_count": str(event_count),
        })

    if not indexes:
        return "No indexes with data found."

    time_range = f"-{days_back}d"
    schema_output = f"### SYSTEM DATA MAP (Last {days_back} Days)\n"

    # 2. For each index, discover key fields via fieldsummary
    for idx in indexes:
        name = idx["name"]

        # Run fieldsummary SPL to get key fields
        spl = (
            f"search index={name} earliest={time_range} "
            f"| head 5 | fieldsummary | where count > 0 | table field"
        )
        try:
            search_resp = _splunk_rest(
                "/services/search/jobs/export",
                method="POST",
                search=spl,
                earliest_time=time_range,
                latest_time="now",
            )
            search_resp.raise_for_status()

            fields = []
            for line in search_resp.text.strip().splitlines():
                try:
                    row = json.loads(line)
                    if "result" in row and "field" in row["result"]:
                        fields.append(row["result"]["field"])
                except json.JSONDecodeError:
                    continue
            fields = fields[:10]
        except Exception as e:
            print(f"[schema] Failed to get fields for index={name}: {e}")
            fields = []

        schema_output += f"\n**Index:** `{name}`\n"
        schema_output += f"- **Event Count:** {idx['total_event_count']}\n"
        if fields:
            schema_output += f"- **Key Fields:** {', '.join(fields)}\n"
        else:
            schema_output += "- **Key Fields:** (unable to discover)\n"

    return schema_output


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    print(get_dynamic_schema())
