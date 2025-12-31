"""Tests for YouTube watch history parser."""

import pytest
from pathlib import Path

from mirror_mcp.parsers.youtube import parse_watch_history


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_watch_history.json"


def test_parse_watch_history():
    """Test parsing Google Takeout watch history JSON."""
    entries = parse_watch_history(str(FIXTURE_PATH))

    assert len(entries) == 5
    assert entries[0].clean_title == "Lo-fi beats to study to"
    assert entries[0].channel_name == "Lofi Girl"


def test_parse_watch_history_extracts_video_id():
    """Test video ID extraction from URL."""
    entries = parse_watch_history(str(FIXTURE_PATH))

    assert entries[0].video_id == "jfKfPfyJRdk"


def test_parse_watch_history_handles_korean():
    """Test parsing entries with Korean titles."""
    entries = parse_watch_history(str(FIXTURE_PATH))

    korean_entries = [e for e in entries if "재즈" in e.clean_title or "케이팝" in e.clean_title]
    assert len(korean_entries) == 2


def test_parse_watch_history_invalid_path():
    """Test handling of invalid file path."""
    with pytest.raises(FileNotFoundError):
        parse_watch_history("/nonexistent/path.json")
