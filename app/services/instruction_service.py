"""Instruction parsing service.

This module provides a simple instruction -> operation parser and a small
wrapper to eventually call Gemini. For now it uses a rule-based fallback if
no `GEMINI_API_KEY` env var is present. Do NOT paste secrets into source;
set `GEMINI_API_KEY` in your environment instead.
"""
from typing import List, Dict, Any
import os
import logging
import json
import re

logger = logging.getLogger(__name__)


def _rule_based_parse(instruction: str) -> List[Dict[str, Any]]:
    """Naive parser that maps keywords to operations for MVP."""
    inst = instruction.lower()
    ops = []
    if "denoise" in inst or "noise" in inst or "remove noise" in inst:
        ops.append({"type": "denoise", "params": {}})
    if "stabil" in inst or "steady" in inst:
        ops.append({"type": "stabilize", "params": {}})
    if "brightness" in inst or "color" in inst or "contrast" in inst:
        params = {}
        if "bright" in inst:
            params["brightness"] = 0.1
        ops.append({"type": "color_adjust", "params": params})
    if "crop" in inst or "resize" in inst or "aspect" in inst:
        if "16:9" in inst:
            ops.append({"type": "crop", "params": {"aspect": "16:9"}})
        else:
            ops.append({"type": "resize", "params": {}})
    if not ops:
        ops.append({"type": "upscale", "params": {}})
    return ops


def parse_instruction(instruction: str) -> List[Dict[str, Any]]:
    """Parse the user's instruction into a list of operations.

    If `GEMINI_API_KEY` is set this will attempt to call Google's Generative
    Language API (text-bison) to convert the instruction into a JSON array of
    operations. If the call fails or the response cannot be parsed, it falls
    back to the internal rule-based parser.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return _rule_based_parse(instruction)

    # Try to call Google's Generative Language API (Generative AI) with API key.
    try:
        try:
            import requests
        except Exception:
            logger.warning("'requests' not available; falling back to rule-based parser")
            return _rule_based_parse(instruction)

        endpoint = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate?key={key}"
        prompt = (
            "You are a service that converts a user's natural-language video-editing "
            "instruction into a JSON array called operations. Each operation must be "
            "an object with keys 'type' (string) and 'params' (object). Only output "
            "the JSON array. Example: [{\"type\":\"denoise\",\"params\":{}},{\"type\":\"crop\",\"params\":{\"aspect\":\"16:9\"}}]"
            "\n\nInstruction:\n" + instruction + "\n\n"
        )

        payload = {"prompt": {"text": prompt}, "temperature": 0}
        resp = requests.post(endpoint, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Extract textual output from known response fields
        text = ""
        if isinstance(data, dict):
            # try common places
            if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
                cand = data["candidates"][0]
                if isinstance(cand, dict):
                    text = cand.get("content") or cand.get("output") or cand.get("text") or ""
            if not text:
                text = data.get("output") or data.get("content") or ""

        if not text:
            # as last resort, stringify response
            text = json.dumps(data)

        # Try to extract JSON array from the text
        m = re.search(r"(\[.*\])", text, re.S)
        ops_json = m.group(1) if m else text

        ops = json.loads(ops_json)
        if isinstance(ops, list):
            return ops
        else:
            logger.warning("Gemini returned non-list, falling back to rule-based parser")
    except Exception as e:
        logger.warning("Gemini call or parsing failed; falling back to rule-based parser: %s", e)

    return _rule_based_parse(instruction)


def interpret_and_enqueue(video_id: str, instruction: str, processor_callable):
    """Interpret an instruction and hand off to the processor.

    `processor_callable` should be a callable accepting `(video_id, operations)`.
    This keeps integration flexible (FastAPI background task or queue worker).
    """
    operations = parse_instruction(instruction)
    # In production, validate operations against an allowlist here.
    processor_callable(video_id, operations)
    return operations
