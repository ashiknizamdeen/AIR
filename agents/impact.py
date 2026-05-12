import json
import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ANTHROPIC_API_KEY, MODEL


def analyze_impact(incident: dict) -> dict:
    """
    Agent 2 — Impact Analysis Agent
    Input: incident dict with responses {user: True/False}
    Returns: affected_count, total, percentage, impact_level, insights
    """
    responses = incident.get("responses", {})
    total = len(responses)
    affected = sum(1 for v in responses.values() if v)
    percentage = round((affected / total * 100), 1) if total > 0 else 0

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are an impact analysis agent for an operations team.

Analyze the following incident response data and return a JSON object with exactly these fields:
- "affected_count": integer number of affected users
- "total_users": integer total users who responded
- "percentage_affected": float percentage
- "impact_level": one of ["Low", "Medium", "High", "Critical"]
- "insights": a list of 2-3 short insight strings about the impact pattern

Incident: {incident.get('title')}
Market: {incident.get('market')}
Severity (from classification): {incident.get('classification', {}).get('severity', 'Unknown') if incident.get('classification') else 'Unknown'}
Affected users: {affected} out of {total} responded ({percentage}%)

Respond ONLY with valid JSON. No markdown.
"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    result = json.loads(raw)

    # Ensure computed values match actual data
    result["affected_count"] = affected
    result["total_users"] = total
    result["percentage_affected"] = percentage

    return result
