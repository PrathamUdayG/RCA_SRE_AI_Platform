# app.py

"""
Backend service orchestrator for Linux Server AI Assistant.
Exposes ask_server(question: str) function to execute the complete workflow.
"""

from datetime import datetime
import time
from typing import Any, Dict

from commands import get_command
from database import create_logs_table, save_log
from llm import explain_output, get_command_key
from parsers import parse_output
from ssh_client import execute_command


def initialize_backend() -> None:
    """Initialize database tables safely."""
    try:
        create_logs_table()
    except Exception as e:
        # DB connection error logged gracefully
        print(f"[Warning] Database initialization failed: {e}")


def ask_server(question: str) -> Dict[str, Any]:
    """
    Orchestrates the complete question answering workflow:
    1. Asks LLM to choose command key.
    2. Validates command key.
    3. Executes command via SSH.
    4. Logs execution to PostgreSQL (graceful error handling).
    5. Parses output into structured JSON.
    6. Generates AI explanation from structured data.
    7. Returns comprehensive response dictionary.
    """
    start_time = time.time()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not question or not question.strip():
        return {
            "success": False,
            "question": question,
            "command_key": None,
            "linux_command": None,
            "raw_output": None,
            "parsed_output": None,
            "answer": "Please provide a valid question.",
            "execution_time_seconds": 0.0,
            "timestamp": timestamp_str,
            "error": "Empty question provided.",
        }

    try:
        # Step 1: Ask Gemini which command key to execute
        llm_response = get_command_key(question)
        command_key = llm_response.get("command_key")

        if command_key == "unsupported":
            duration = round(time.time() - start_time, 2)
            return {
                "success": False,
                "question": question,
                "command_key": "unsupported",
                "linux_command": None,
                "raw_output": None,
                "parsed_output": None,
                "answer": "Sorry, I cannot answer that question with the current command set.",
                "execution_time_seconds": duration,
                "timestamp": timestamp_str,
                "error": "Unsupported command requested.",
            }

        # Step 2: Validate command key in registry
        command_info = get_command(command_key)
        if command_info is None:
            duration = round(time.time() - start_time, 2)
            return {
                "success": False,
                "question": question,
                "command_key": command_key,
                "linux_command": None,
                "raw_output": None,
                "parsed_output": None,
                "answer": f"Command key '{command_key}' is not registered.",
                "execution_time_seconds": duration,
                "timestamp": timestamp_str,
                "error": f"Command key '{command_key}' not found.",
            }

        linux_command = command_info["command"]

        # Step 3: Execute SSH command
        result = execute_command(linux_command)
        raw_output = result.get("output", "")
        error_msg = result.get("error", "")

        # Step 4: Save execution log to database (non-blocking failure)
        try:
            save_log(
                host=result.get("host", "unknown"),
                command=linux_command,
                output=raw_output,
                error=error_msg,
            )
        except Exception as db_err:
            print(f"[Warning] Failed to log to DB: {db_err}")

        # Step 5: Parse raw output into structured JSON
        parsed_output = parse_output(linux_command, raw_output)

        # Step 6: Generate AI explanation using Gemini
        answer = explain_output(
            user_question=question,
            command=linux_command,
            structured_output=parsed_output,
        )

        duration = round(time.time() - start_time, 2)

        return {
            "success": True,
            "question": question,
            "command_key": command_key,
            "linux_command": linux_command,
            "raw_output": raw_output,
            "parsed_output": parsed_output,
            "answer": answer,
            "execution_time_seconds": duration,
            "timestamp": timestamp_str,
            "error": error_msg if error_msg else None,
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return {
            "success": False,
            "question": question,
            "command_key": None,
            "linux_command": None,
            "raw_output": None,
            "parsed_output": None,
            "answer": "An error occurred while processing your request.",
            "execution_time_seconds": duration,
            "timestamp": timestamp_str,
            "error": str(e),
        }


# Initialize DB when module is imported or loaded
initialize_backend()