import os

import requests


def _jira_rest(endpoint: str, method: str = "GET", **params) -> requests.Response:
    """Call a Jira REST API endpoint with basic auth.

    Args:
        endpoint: The REST path, e.g. "/rest/api/2/project".
        method: HTTP method (GET or POST).
        **params: Extra query/form params forwarded to the request.

    Returns:
        The HTTP response object.
    """
    base_url = os.environ.get("JIRA_URL", "").rstrip("/")
    username = os.environ.get("JIRA_USERNAME", "")
    api_token = os.environ.get("JIRA_API_TOKEN", "")

    url = f"{base_url}{endpoint}"
    auth = (username, api_token)
    headers = {"Accept": "application/json"}

    if method.upper() == "GET":
        return requests.get(url, params=params, auth=auth, headers=headers)
    return requests.post(url, json=params, auth=auth, headers=headers)


def get_jira_schema() -> str:
    """Discover available Jira projects and issue types via REST API.

    Returns:
        A markdown string describing the discovered Jira schema.
    """
    schema_output = "### JIRA INSTANCE SCHEMA\n"

    # 1. List all projects
    try:
        resp = _jira_rest("/rest/api/2/project")
        resp.raise_for_status()
        projects = resp.json()

        schema_output += "\n**Projects:**\n"
        for project in projects:
            schema_output += f"- `{project['key']}` — {project['name']}\n"
    except Exception as e:
        print(f"[schema] Failed to list Jira projects: {e}")
        schema_output += "\n**Projects:** (unable to discover)\n"

    # 2. List all issue types
    try:
        resp = _jira_rest("/rest/api/2/issuetype")
        resp.raise_for_status()
        issue_types = resp.json()

        standard = [it["name"] for it in issue_types if not it.get("subtask")]
        subtasks = [it["name"] for it in issue_types if it.get("subtask")]

        schema_output += "\n**Issue Types:**\n"
        if standard:
            schema_output += f"- Standard: {', '.join(standard)}\n"
        if subtasks:
            schema_output += f"- Subtasks: {', '.join(subtasks)}\n"
    except Exception as e:
        print(f"[schema] Failed to list Jira issue types: {e}")
        schema_output += "\n**Issue Types:** (unable to discover)\n"

    return schema_output


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    print(get_jira_schema())
