import anthropic
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ANTHROPIC_API_KEY, MODEL


def generate_report(incident: dict) -> str:
    """
    Agent 3 — Report Generation Agent
    Returns: a structured markdown incident report string
    """
    classification = incident.get("classification") or {}
    impact = incident.get("impact_analysis") or {}
    responses = incident.get("responses", {})

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are an incident report writer for an operations team.

Generate a professional incident report in Markdown format using the data below.

Include these sections:
1. **Incident Summary** — brief description of what happened
2. **Classification** — category, severity, priority
3. **Impact Assessment** — how many users affected, impact level, key insights
4. **Timeline** — when reported (use the created_at field)
5. **Recommended Actions** — 3-5 concrete action items to resolve and prevent recurrence
6. **Status** — current status

Keep it concise and professional. Use tables where helpful.

---
Incident ID: {incident.get('id')}
Title: {incident.get('title')}
Description: {incident.get('description')}
Market: {incident.get('market')}
Team Lead: {incident.get('team_lead')}
Created At: {incident.get('created_at')}
Status: {incident.get('status')}

Classification:
- Category: {classification.get('category', 'N/A')}
- Severity: {classification.get('severity', 'N/A')}
- Priority: {classification.get('priority', 'N/A')}
- Reasoning: {classification.get('reasoning', 'N/A')}

Impact:
- Affected: {impact.get('affected_count', 0)} / {impact.get('total_users', 0)} users ({impact.get('percentage_affected', 0)}%)
- Impact Level: {impact.get('impact_level', 'N/A')}
- Insights: {impact.get('insights', [])}
---

Return ONLY the markdown report. No extra commentary.
"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
