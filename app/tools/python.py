# app/tools/python.py
import sys
import io
import traceback
from langchain_core.tools import tool
import pandas as pd  # Pre-import common libs
import numpy as np

# A global dictionary to hold session variables.
# Key = email (or unique session ID), Value = globals dictionary
SESSION_GLOBALS = {}


@tool
def python_tool(code: str, session_id: str) -> str:
    """
    Executes Python code in a stateful environment (variables persist).
    ALWAYS print() the result you want to see.

    Args:
        code: Valid python code.
        session_id: The user's email or session identifier.
    """
    # Initialize session if not exists
    if session_id not in SESSION_GLOBALS:
        SESSION_GLOBALS[session_id] = {"pd": pd, "np": np, "__builtins__": __builtins__}

    local_scope = SESSION_GLOBALS[session_id]

    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        # execute code using the persistent scope
        exec(code, local_scope)

        output = redirected_output.getvalue()
        return (
            output.strip()
            if output.strip()
            else "Code executed. (No output provided. Did you forget to print?)"
        )

    except Exception:
        return f"Runtime Error:\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
