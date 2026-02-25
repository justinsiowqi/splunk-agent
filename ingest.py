import argparse
import io
import json
import os
import sys
import zipfile

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_DATASET_URL = "https://github.com/UraSecTeam/mordor/raw/master/datasets/small/aws/collection/ec2_proxy_s3_exfiltration.zip"


def ingest_data(dataset_url, index):
    hec_token = os.environ.get("SPLUNK_HEC_TOKEN")
    if not hec_token:
        print("Error: SPLUNK_HEC_TOKEN environment variable is not set.")
        print("Usage: export SPLUNK_HEC_TOKEN=<your_hec_token> && python ingest.py")
        sys.exit(1)

    hec_url = os.environ.get("SPLUNK_HEC_URL")
    if not hec_url:
        print("Error: SPLUNK_HEC_URL environment variable is not set.")
        print("Usage: export SPLUNK_HEC_URL=<your_hec_url> && python ingest.py")
        sys.exit(1)

    print(f"[*] Downloading dataset from {dataset_url}...")
    r = requests.get(dataset_url)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for filename in z.namelist():
            if not filename.endswith(".json"):
                continue

            print(f"[*] Processing {filename}...")
            with z.open(filename) as f:
                events = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    events.append(json.dumps({
                        "index": index,
                        "event": record,
                    }))

            print(f"[*] Sending {len(events)} events to Splunk...")
            headers = {"Authorization": f"Splunk {hec_token}"}
            resp = requests.post(
                hec_url, data="\n".join(events), headers=headers, verify=False,
            )
            if resp.status_code == 200:
                print(f"[+] Success! {len(events)} events ingested into index='{index}'.")
            else:
                print(f"[-] Error {resp.status_code}: {resp.text}")
                sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a dataset into Splunk via HEC.")
    parser.add_argument("index", help="Splunk index name (must match the index created in Splunk)")
    parser.add_argument("--url", default=DEFAULT_DATASET_URL, help="Dataset zip URL")
    args = parser.parse_args()
    ingest_data(args.url, args.index)