"""Tests for app/utils/answers.py"""

import json
from pathlib import Path

import pytest

from app.utils.answers import save_correct_answer


def test_creates_new_file_and_appends(tmp_path: Path):
    target = tmp_path / "answers.json"

    save_correct_answer("http://quiz/1", {"answer": 42}, path=target)

    data = json.loads(target.read_text())
    assert data == [{"url": "http://quiz/1", "answer_payload": {"answer": 42}}]


def test_upserts_existing_entry(tmp_path: Path):
    target = tmp_path / "answers.json"
    target.write_text(
        json.dumps([{"url": "http://quiz/1", "answer_payload": {"answer": "old"}}])
    )

    save_correct_answer("http://quiz/1", {"answer": "new"}, path=target)

    data = json.loads(target.read_text())
    assert len(data) == 1
    assert data[0]["answer_payload"] == {"answer": "new"}


@pytest.mark.parametrize("url", ["", None])
def test_noop_when_url_missing(tmp_path: Path, url):
    target = tmp_path / "answers.json"

    save_correct_answer(url, {"answer": 99}, path=target)

    assert not target.exists()
