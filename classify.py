import base64
import json
import re

import streamlit as st
from anthropic import Anthropic

from prompt import CLASSIFICATION_PROMPT

MODEL = "claude-sonnet-4-6"


def _client() -> Anthropic:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("Missing ANTHROPIC_API_KEY. See .streamlit/secrets.toml.example.")
        st.stop()
    return Anthropic(api_key=api_key)


def classify_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    client = _client()
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {"type": "text", "text": CLASSIFICATION_PROMPT},
                ],
            }
        ],
    )
    text = response.content[0].text
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {
        "category": "other",
        "confidence": "low",
        "reasoning": "Could not parse classifier response.",
        "notable_details": text[:200],
    }
