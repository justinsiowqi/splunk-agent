import argparse
import io
import json
import os
import sys
import time
import zipfile
from datetime import datetime, timezone

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_DATASET_URL = "https://github.com/UraSecTeam/mordor/raw/master/datasets/small/aws/collection/ec2_proxy_s3_exfiltration.zip"

TIMESTAMP_FIELDS = ["@timestamp", "eventTime", "time", "timestamp"]


def parse_timestamp(record):
    for field in TIMESTAMP_FIELDS:
        val = record.get(field)
        if not val:
            continue
        if isinstance(val, (int, float)):
            return float(val)
        try:
            dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            continue
    return None


def rewrite_timestamps(record, new_epoch):
    shifted_dt = datetime.fromtimestamp(new_epoch, tz=timezone.utc)
    shifted_iso = shifted_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for field in TIMESTAMP_FIELDS:
        if field in record:
            if isinstance(record[field], (int, float)):
                record[field] = new_epoch
            else:
                record[field] = shifted_iso


def send_event(hec_url, hec_token, index, record, event_time):
    payload = json.dumps({
        "time": event_time,
        "index": index,
        "event": record,
    })
    headers = {"Authorization": f"Splunk {hec_token}"}
    resp = requests.post(hec_url, data=payload, headers=headers, verify=False)
    if resp.status_code != 200:
        print(f"[-] Error {resp.status_code}: {resp.text}")
        sys.exit(1)


def load_records(dataset_url):
    print(f"[*] Downloading dataset from {dataset_url}...")
    r = requests.get(dataset_url)
    r.raise_for_status()

    records = []
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for filename in sorted(z.namelist()):
            if not filename.endswith(".json"):
                continue
            print(f"[*] Loading {filename}...")
            with z.open(filename) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    records.append(json.loads(line))

    parsed = [(parse_timestamp(rec), rec) for rec in records]
    parsed.sort(key=lambda x: x[0] if x[0] is not None else 0)
    return parsed


def fmt_duration(seconds):
    seconds = int(seconds)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def info(dataset_url):
    parsed = load_records(dataset_url)
    valid_ts = [ts for ts, _ in parsed if ts is not None]

    if not valid_ts:
        print("[-] No parseable timestamps found in dataset.")
        sys.exit(1)

    span = max(valid_ts) - min(valid_ts)
    first = datetime.fromtimestamp(min(valid_ts), tz=timezone.utc).isoformat()
    last = datetime.fromtimestamp(max(valid_ts), tz=timezone.utc).isoformat()

    print(f"\n  Events   : {len(parsed)}")
    print(f"  First    : {first}")
    print(f"  Last     : {last}")
    print(f"  Span     : {fmt_duration(span)}\n")
    print(f"  Estimated replay duration by speed:")
    for speed in [1, 10, 30, 60, 120, 300]:
        print(f"    --speed {speed:<5} -> {fmt_duration(span / speed)}")
    print()


def replay_data(dataset_url, index, speed):
    hec_token = os.environ.get("SPLUNK_HEC_TOKEN")
    if not hec_token:
        print("Error: SPLUNK_HEC_TOKEN environment variable is not set.")
        sys.exit(1)

    hec_url = os.environ.get("SPLUNK_HEC_URL")
    if not hec_url:
        print("Error: SPLUNK_HEC_URL environment variable is not set.")
        sys.exit(1)

    parsed = load_records(dataset_url)
    valid_ts = [ts for ts, _ in parsed if ts is not None]

    if not valid_ts:
        print("[-] No parseable timestamps found in dataset.")
        sys.exit(1)

    min_original = min(valid_ts)
    now = datetime.now(timezone.utc).timestamp()
    shift = now - min_original  # first event starts at now

    print(f"[*] Replaying {len(parsed)} events at {speed}x speed. Press Ctrl+C to stop.")

    for i, (original_ts, record) in enumerate(parsed):
        if original_ts is None:
            original_ts = min_original  # fallback: send immediately

        # Compress the time gap by the speed factor so Splunk timestamps match wall clock
        compressed_offset = (original_ts - min_original) / speed
        event_time = now + compressed_offset

        # Send at the same rate as the compressed timestamps
        wall_send_time = now + compressed_offset
        wait = wall_send_time - time.time()
        if wait > 0:
            time.sleep(wait)

        rewrite_timestamps(record, event_time)
        send_event(hec_url, hec_token, index, record, event_time)
        print(f"[+] [{i+1}/{len(parsed)}] Sent event at {datetime.fromtimestamp(event_time, tz=timezone.utc).isoformat()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replay a dataset into Splunk in real-time, preserving relative event timing."
    )
    parser.add_argument("index", nargs="?", help="Splunk index name (not required with --info)")
    parser.add_argument("--url", default=DEFAULT_DATASET_URL, help="Dataset zip URL")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Playback speed multiplier (e.g. 10 = 10x faster, default: 1.0)")
    parser.add_argument("--info", action="store_true",
                        help="Show dataset time span and estimated durations, then exit")
    args = parser.parse_args()

    if args.info:
        info(args.url)
    else:
        if not args.index:
            parser.error("index is required unless --info is used")
        replay_data(args.url, args.index, args.speed)
