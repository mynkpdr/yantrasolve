# app/tools/python.py
import sys
import io
import traceback
from langchain_core.tools import tool
import pandas as pd  # Pre-import common libs
import numpy as np

# A global dictionary to hold session variables.
# We use a single global scope since the app handles one quiz at a time per session
GLOBAL_SCOPE = {"pd": pd, "np": np, "__builtins__": __builtins__}


def reset_python_session():
    """Reset the Python session globals for a new quiz."""
    global GLOBAL_SCOPE
    GLOBAL_SCOPE = {"pd": pd, "np": np, "__builtins__": __builtins__}


@tool
def python_tool(code: str):
    """
    Args:
        code: Valid Python code to execute. Must use print() to output results.
    """
    global GLOBAL_SCOPE

    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        # execute code using the persistent scope
        exec(code, GLOBAL_SCOPE)

        output = redirected_output.getvalue()
        return (
            output.strip()
            if output.strip()
            else "Code executed. (No output provided. Did you forget to print?)"
        )

    except Exception:
        error_msg = traceback.format_exc()
        # Try to give a hint if it's a common error
        if "NameError" in error_msg:
            error_msg += "\nHint: Did you define the variable in a previous step? Remember session is stateful."
        if "ModuleNotFoundError" in error_msg:
            error_msg += "\nHint: The module may not be installed. Try using an alternative or install it via pip."
        return f"Runtime Error:\n{error_msg}. Please fix the code and try again."
    finally:
        sys.stdout = old_stdout


