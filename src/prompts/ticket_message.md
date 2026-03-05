Create a Jira incident ticket for the following threat hunting investigation.

## Hypothesis
{hypothesis}

## Discovery Findings
{discovery_findings}

## Investigation Evidence
{investigation_evidence}

## Instructions
Create a ticket using all the evidence above. Map the priority based on severity:
- Active compromise with confirmed data exfiltration -> Highest
- Confirmed privilege escalation or unauthorized access -> High
- Anomalous patterns without confirmed impact -> Medium
- Informational findings or low-confidence signals -> Low

Include the label `threat-hunting` along with any relevant category labels (e.g., `data-exfiltration`, `credential-compromise`, `lateral-movement`).

Populate the description with the incident timeline, IOCs, evidence summary, and recommended remediation actions from the investigation evidence.
