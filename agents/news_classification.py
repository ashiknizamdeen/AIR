import json
import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ANTHROPIC_API_KEY, MODEL


def classify_news(title: str, description: str) -> dict:
    """
    News Risk Classification Agent
    Returns: category, risk_level, reasoning
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a risk assessment agent for an operations team.

Analyze this news alert and return a JSON object with exactly these fields:
- "category": one of ["Market Alert", "Regulatory Notice", "Operational Advisory", "Security Notice", "System Update", "Other"]
- "risk_level": one of ["Low", "Medium", "High", "Critical"]
- "reasoning": a brief 1-sentence explanation of the risk assessment

News Title: {title}
News Description: {description}

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON.
"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    return json.loads(raw)
