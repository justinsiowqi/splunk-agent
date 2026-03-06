# Data Scripts

All scripts live in `data/` and read credentials from `.env` automatically.

## `ingest.py` — Bulk ingest

Downloads a zipped dataset from a URL and sends all events to Splunk at once with their original timestamps. Useful for loading historical data quickly.

```bash
# Ingest the default Mordor dataset into the 'mordor' index
python data/ingest.py mordor

# Ingest a custom dataset
python data/ingest.py mordor --url https://example.com/dataset.zip
```

## `replay.py` — Real-time replay

Streams events into Splunk one by one, preserving the relative time gaps between events. Timestamps are shifted so the first event starts at the current time. Use `--speed` to compress the timeline for demos.

```bash
# Check the dataset time span and estimated durations before running
python data/replay.py --info

# Replay at real-time speed
python data/replay.py mordor

# Replay at 10x speed (a 25-minute attack plays out in ~2.5 minutes)
python data/replay.py mordor --speed 10

# Replay a custom dataset
python data/replay.py mordor --speed 10 --url https://example.com/dataset.zip
```

## `delete.py` — Delete index events

Deletes all events from a Splunk index using the management API. Automatically grants the `can_delete` role to the configured user if not already assigned.

```bash
# Delete all events from the 'mordor' index
python data/delete.py mordor

# Delete events matching a specific filter
python data/delete.py mordor --query "source=aws"
```
