"""
Call LLM Tool - Uses Gemini 2.5 Flash for multimodal file understanding.

Supports: Images, PDFs, Audio, Video files.
"""

import os
from pathlib import Path
from typing import List

from langchain_core.tools import tool

from app.utils.logging import logger
from app.utils.gemini import (
    GEMINI_MODEL,
    get_gemini_client,
    create_data_uri,
    is_text_file,
)


# Constants
MAX_FILE_SIZE_MB = 20
SYSTEM_PROMPT = "You are an expert file analyzer. Extract information accurately and concisely. For numerical answers, provide just the number. For text extraction, be precise and complete."


def _build_file_content(file_path: str) -> dict:
    """Build content dict for a single file."""
    if is_text_file(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            return {
                "type": "text",
                "text": f"\n\n--- FILE: {Path(file_path).name} ---\n{file_content}\n--- END FILE ---",
            }
        except UnicodeDecodeError:
            pass  # Fall through to binary handling

    # Binary files (images, PDFs, audio, video)
    data_uri = create_data_uri(file_path)
    return {"type": "image_url", "image_url": {"url": data_uri}}


def _validate_files(file_paths: List[str]) -> str | None:
    """Validate files exist and total size is within limits. Returns error message or None."""
    for fp in file_paths:
        if not os.path.exists(fp):
            return f"Error: File not found: {fp}"

    total_size_mb = sum(os.path.getsize(fp) for fp in file_paths) / (1024 * 1024)
    if total_size_mb > MAX_FILE_SIZE_MB:
        return f"Error: Total file size too large ({total_size_mb:.2f}MB). Maximum is {MAX_FILE_SIZE_MB}MB."

    return None


def _call_gemini(prompt: str, file_paths: List[str]) -> str:
    """Core function to call Gemini LLM with files."""
    # Validate files
    error = _validate_files(file_paths)
    if error:
        return error

    logger.info(f"Calling Gemini LLM for {len(file_paths)} file(s)")

    # Build message content
    content = [{"type": "text", "text": prompt}]
    for file_path in file_paths:
        content.append(_build_file_content(file_path))

    # Make the API call
    client = get_gemini_client()
    completion = client.chat.completions.create(
        model=GEMINI_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )

    result = completion.choices[0].message.content
    logger.info(f"Gemini LLM response received (length: {len(result)})")
    return result


@tool
def call_llm_tool(file_path: str, prompt: str) -> str:
    """
    Analyze a file using Gemini 2.5 Flash multimodal LLM.

    Only use this tool to:
    - Extract text/OCR from images
    - Understand PDF documents
    - Transcribe audio files
    - Analyze video content
    - Understand charts/graphs
    - Any other file understanding task

    Args:
        file_path: Absolute path to the file to analyze (image, PDF, audio, video, etc.)
        prompt: The question or instruction about the file content

    Returns:
        LLM response as a string with the analysis results
    """
    try:
        return _call_gemini(prompt, [file_path])
    except Exception as e:
        logger.error(f"Error calling Gemini LLM: {e}")
        return f"Error calling LLM: {str(e)}"


@tool
def call_llm_with_multiple_files_tool(file_paths: List[str], prompt: str) -> str:
    """
    Analyze multiple files together using Gemini 2.5 Flash multimodal LLM.

    Use this when you need to:
    - Compare multiple images/documents
    - Combine data from multiple sources
    - Cross-reference information across files

    Args:
        file_paths: List of absolute paths to files to analyze
        prompt: The question or instruction about the files

    Returns:
        LLM response as a string with the analysis results
    """
    try:
        return _call_gemini(prompt, file_paths)
    except Exception as e:
        logger.error(f"Error calling Gemini LLM: {e}")
        return f"Error calling LLM: {str(e)}"
