# llm.py

import json
import os
import re
from dotenv import load_dotenv
import requests

from commands import COMMANDS
from shared.config import get_settings

load_dotenv()


def _call_llm_api(prompt: str) -> str:
    """Helper calling active LLM API endpoint."""
    settings = get_settings()
    api_key = settings.llm.api_key
    model_name = settings.llm.default_model

    if not api_key:
        return ""

    url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1000,
            "temperature": 0.1,
            "return_full_text": False,
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("generated_text", "")
            elif isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"]
            return resp.text
        return ""
    except Exception:
        return ""


def build_system_prompt():
    """
    Dynamically builds the system prompt from the
    commands available in commands.py
    """

    available_commands = ""

    for key, value in COMMANDS.items():
        examples_list = value.get("examples", [])
        examples_str = f" (Examples: {', '.join(examples_list)})" if examples_list else ""
        available_commands += (
            f"- {key}: {value['description']}{examples_str}\n"
        )

    prompt = f"""
You are a Linux Server Assistant.

Your job is to map the user's question to ONE command key.

Available command keys:

{available_commands}

Rules:

1. Return ONLY JSON.
2. Never return Linux commands.
3. Return ONLY the command key.
4. If no command matches, return:

{{
    "command_key":"unsupported"
}}

Example:

User:
How much RAM is available?

Response:

{{
    "command_key":"memory_usage"
}}
"""

    return prompt


def get_command_key(user_question: str):
    prompt = f"{build_system_prompt()}\n\nUser Question:\n{user_question}"
    raw_text = _call_llm_api(prompt).strip()

    try:
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)
        return json.loads(raw_text)
    except Exception:
        return {
            "command_key": "unsupported"
        }


def explain_output(
    user_question: str,
    command: str,
    structured_output: dict
):
    """
    Uses LLM to explain the Linux command output
    in simple English using structured JSON data.
    """

    formatted_data = json.dumps(structured_output, indent=2)

    prompt = f"""
You are a Linux server assistant.

The user asked:

{user_question}

The following Linux command was executed:

{command}

Its structured output (JSON format) is:

{formatted_data}

Instructions:

- Answer the user's original question.
- Explain the output in simple English.
- Be concise.
- If useful, include important numbers.
- Do not invent information.
- Do not mention commands unless necessary.
"""

    response_text = _call_llm_api(prompt)
    return response_text.strip() if response_text else "Output analyzed from structured telemetry."