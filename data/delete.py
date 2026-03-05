import argparse
import os
import sys

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def grant_can_delete(mgmt_url, username, password):
    resp = requests.get(
        f"{mgmt_url}/services/authentication/users/{username}",
        params={"output_mode": "json"},
        auth=(username, password),
        verify=False,
    )
    resp.raise_for_status()
    roles = resp.json()["entry"][0]["content"]["roles"]
    if "can_delete" not in roles:
        roles.append("can_delete")
        patch = requests.post(
            f"{mgmt_url}/services/authentication/users/{username}",
            data={"roles": roles, "output_mode": "json"},
            auth=(username, password),
            verify=False,
        )
        patch.raise_for_status()
        print(f"[*] Granted 'can_delete' role to '{username}'.")


def delete_data(index, query="*"):
    host = os.environ.get("SPLUNK_HOST", "localhost")
    port = os.environ.get("SPLUNK_MGMT_PORT", "8089")
    mgmt_url = f"https://{host}:{port}"

    username = os.environ.get("SPLUNK_USERNAME")
    if not username:
        print("Error: SPLUNK_USERNAME environment variable is not set.")
        sys.exit(1)

    password = os.environ.get("SPLUNK_PASSWORD")
    if not password:
        print("Error: SPLUNK_PASSWORD environment variable is not set.")
        sys.exit(1)

    grant_can_delete(mgmt_url, username, password)

    search = f"search index={index} {query} | delete"
    print(f"[*] Running delete search: {search}")

    resp = requests.post(
        f"{mgmt_url}/services/search/jobs",
        data={"search": search, "output_mode": "json"},
        auth=(username, password),
        verify=False,
    )

    if resp.status_code not in (200, 201):
        print(f"[-] Error creating search job {resp.status_code}: {resp.text}")
        sys.exit(1)

    sid = resp.json()["sid"]
    print(f"[*] Search job created: sid={sid}")

    # Poll until the job is done
    while True:
        status_resp = requests.get(
            f"{mgmt_url}/services/search/jobs/{sid}",
            params={"output_mode": "json"},
            auth=(username, password),
            verify=False,
        )
        status_resp.raise_for_status()
        job = status_resp.json()["entry"][0]["content"]
        dispatch_state = job["dispatchState"]

        if dispatch_state == "DONE":
            event_count = job.get("eventCount", 0)
            print(f"[+] Done. {event_count} events deleted from index='{index}'.")
            break
        elif dispatch_state == "FAILED":
            print(f"[-] Search job failed: {job.get('messages', '')}")
            sys.exit(1)
        else:
            print(f"[*] Job state: {dispatch_state}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete events from a Splunk index.")
    parser.add_argument("index", help="Splunk index name to delete events from")
    parser.add_argument("--query", default="*", help="Additional search filter (default: * deletes all events)")
    args = parser.parse_args()
    delete_data(args.index, args.query)
