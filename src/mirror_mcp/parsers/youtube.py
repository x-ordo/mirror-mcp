"""Google Takeout YouTube watch history parser."""

import json
from datetime import datetime
from pathlib import Path

from ..models import ChannelInfo, WatchHistoryEntry


def parse_watch_history(file_path: str) -> list[WatchHistoryEntry]:
    """
    Parse Google Takeout watch-history.json file.

    Handles edge cases:
    - Missing subtitles (ads)
    - Missing titleUrl (deleted videos)
    - Various timestamp formats

    Args:
        file_path: Path to the watch-history.json file

    Returns:
        List of WatchHistoryEntry objects
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Watch history file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    entries = []
    for item in raw_data:
        # Skip non-YouTube entries (YouTube Music has different header)
        if item.get("header") not in ["YouTube", "YouTube Music"]:
            continue

        # Parse subtitles (channel info)
        subtitles = []
        for sub in item.get("subtitles", []):
            subtitles.append(
                ChannelInfo(
                    name=sub.get("name", "Unknown"),
                    url=sub.get("url"),
                )
            )

        # Parse timestamp
        time_str = item.get("time", "")
        try:
            # Handle both 'Z' suffix and timezone offsets
            timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except ValueError:
            continue  # Skip entries with invalid timestamps

        entry = WatchHistoryEntry(
            header=item.get("header", "YouTube"),
            title=item.get("title", "Unknown"),
            titleUrl=item.get("titleUrl"),
            subtitles=subtitles,
            time=timestamp,
            products=item.get("products", ["YouTube"]),
            activityControls=item.get("activityControls", []),
        )
        entries.append(entry)

    return entries
