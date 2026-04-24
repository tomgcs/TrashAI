import base64
import hashlib
import json
import re
from io import BytesIO

import streamlit as st
from anthropic import Anthropic
from PIL import Image

from prompt import CLASSIFICATION_PROMPT

MODEL = "claude-sonnet-4-6"
_PLACEHOLDER_KEYS = {"", "REPLACE_ME_WITH_YOUR_KEY", "sk-ant-..."}
_API_MAX_DIMENSION = 1600
_API_JPEG_QUALITY = 85

_STUB_CATEGORIES = [
    "curbside_trash",
    "bulk_item",
    "illegal_dumping",
    "overflowing_basket",
    "dog_waste",
    "graffiti",
    "pothole",
    "abandoned_vehicle",
]


def is_stub_mode() -> bool:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    return api_key in _PLACEHOLDER_KEYS


def _client() -> Anthropic:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    return Anthropic(api_key=api_key)


def classify_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    if is_stub_mode():
        return _stub_classify(image_bytes)

    api_bytes, api_media_type = _prepare_for_api(image_bytes)
    client = _client()
    b64 = base64.standard_b64encode(api_bytes).decode("utf-8")
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": api_media_type, "data": b64},
                    },
                    {"type": "text", "text": CLASSIFICATION_PROMPT},
                ],
            }
        ],
    )
    text = response.content[0].text
    return _parse_json(text)


def _prepare_for_api(image_bytes: bytes) -> tuple:
    img = Image.open(BytesIO(image_bytes))
    img.thumbnail((_API_MAX_DIMENSION, _API_MAX_DIMENSION))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=_API_JPEG_QUALITY)
    return buf.getvalue(), "image/jpeg"


def _stub_classify(image_bytes: bytes) -> dict:
    digest = hashlib.sha1(image_bytes).digest()
    category = _STUB_CATEGORIES[digest[0] % len(_STUB_CATEGORIES)]
    return {
        "category": category,
        "confidence": "medium",
        "reasoning": "Stub classifier — Claude Vision is disabled until the API key is configured.",
        "notable_details": "Stub mode: category chosen deterministically from the image hash for demo purposes.",
    }


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
