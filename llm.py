# llm.py

import json
import os
import re

from dotenv import load_dotenv
from google import genai

from commands import COMMANDS

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


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

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
{build_system_prompt()}

User Question:

{user_question}
"""
    )

    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            # Strip backticks and json identifier
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
    Uses Gemini to explain the Linux command output
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

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()