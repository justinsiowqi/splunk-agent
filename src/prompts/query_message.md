I'm conducting a threat hunting investigation and need you to run SPL queries to trace the attack chain.

## Hypothesis
{hypothesis}

## Discovery Findings
The discovery phase found the following about the environment:
{discovery_findings}

## What I Need
Based on the hypothesis and discovery findings above, run SPL queries to investigate:
1. Identify the anomalous entities (users, IPs, roles) — look for unusual API call volumes, unexpected source IPs, or abnormal user behavior.
2. Track privilege escalation (e.g., AssumeRole events, policy changes, credential modifications).
3. Track data access patterns (e.g., S3 operations, file downloads, sensitive resource access).
4. Establish a chronological timeline of the suspicious activity.

Provide your findings as:
- **Incident Timeline**: Chronological events with timestamps.
- **Attack Chain**: Step-by-step reconstruction of the attack.
- **Indicators of Compromise (IOCs)**: Source IPs, compromised users/roles, affected resources, suspicious user agents.
- **Evidence Summary**: The SPL queries you ran and what each revealed.
