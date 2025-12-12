"""Persist correct quiz answers to answers.json."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app.config.settings import settings

DEFAULT_PATH = Path(settings.LOGS_DIR) / "answers.json"


def save_correct_answer(url: str, payload: Any, path: Path = DEFAULT_PATH) -> None:
    if not url:
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    data: List[Dict[str, Any]] = []
    if path.exists():
        try:
            existing = json.load(path.open())
            if isinstance(existing, list):
                data = [x for x in existing if isinstance(x, dict)]
        except Exception:
            pass

    for row in data:
        if row.get("url") == url:
            row["answer_payload"] = payload
            break
    else:
        data.append({"url": url, "answer_payload": payload})

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
