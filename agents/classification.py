import json
import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ANTHROPIC_API_KEY, MODEL


def classify_incident(title: str, description: str,
                      metrics: list = None, metric_criticalities: list = None) -> dict:
    """
    Agent 1 — Classification Agent
    Returns: category, severity, priority, reasoning
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    metric_context = ""
    if metrics:
        lines = []
        for i, m in enumerate(metrics):
            crit = (metric_criticalities or [])[i] if metric_criticalities and i < len(metric_criticalities) else None
            if crit:
                lines.append(f"  - {m} (pre-defined criticality: {crit})")
            else:
                lines.append(f"  - {m} (assess criticality from operational context)")
        metric_context = (
            "\nAffected Metrics (assess combined impact — multiple affected metrics "
            "generally indicate higher severity):\n" + "\n".join(lines)
        )

    prompt = f"""You are an incident classification agent for an operations team.

Analyze this incident and return a JSON object with exactly these fields:
- "category": one of ["Application Issue", "Network Issue", "Data Issue", "Infrastructure Issue", "Access Issue", "Performance Issue", "Other"]
- "severity": one of ["Low", "Medium", "High", "Critical"]
- "priority": one of ["P1", "P2", "P3", "P4"] where P1 is highest
- "reasoning": a brief 1-2 sentence explanation
- "remediation_actions": a list of 3-4 short imperative action steps a team lead should take to resolve this incident (each step under 12 words, plain language, no numbering)

When multiple metrics are affected, assess their combined criticality — more affected metrics with higher individual criticality should push severity upward.

Incident Title: {title}
Incident Description: {description}{metric_context}

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON.
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
    return json.loads(raw)
