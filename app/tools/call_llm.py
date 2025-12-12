"""LLM tools for multimodal file analysis using Gemini."""

import os
from pathlib import Path
from typing import List
from langchain_core.tools import tool
from app.config.settings import settings
from app.utils.logging import logger
from app.utils.gemini import (
    get_gemini_client,
    create_data_uri,
    is_text_file,
)

SYSTEM_PROMPT = (
    "You are an expert file analyzer. Extract information accurately and concisely."
)


def _build_file_content(file_path: str) -> dict:
    """Build content dict for a single file (text or binary)."""
    if is_text_file(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return {
                    "type": "text",
                    "text": f"\n--- FILE: {Path(file_path).name} ---\n{f.read()}\n--- END ---",
                }
        except UnicodeDecodeError:
            pass  # Fall through to binary handling
    return {"type": "image_url", "image_url": {"url": create_data_uri(file_path)}}


def _validate_files(file_paths: List[str]) -> str | None:
    """Validate files exist and total size is within limits."""
    for fp in file_paths:
        if not os.path.exists(fp):
            return f"Error: File not found: {fp}"
    total_size_mb = sum(os.path.getsize(fp) for fp in file_paths) / (1024 * 1024)
    if total_size_mb > settings.MAX_FILE_SIZE_MB:
        return f"Error: Total file size too large ({total_size_mb:.2f}MB). Max is {settings.MAX_FILE_SIZE_MB}MB."
    return None


def _call_gemini(prompt: str, file_paths: List[str]) -> str:
    """Core function to call Gemini LLM with files."""
    if error := _validate_files(file_paths):
        return error

    logger.info(f"Calling Gemini LLM for {len(file_paths)} file(s)")
    content = [{"type": "text", "text": prompt}] + [
        _build_file_content(fp) for fp in file_paths
    ]

    result = (
        get_gemini_client()
        .chat.completions.create(
            model=settings.GEMINI_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        )
        .choices[0]
        .message.content
    )

    logger.info(f"Gemini response received (length: {len(result)})")
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
