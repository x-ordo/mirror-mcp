"""Time-based viewing pattern analyzer."""

import math
from collections import Counter, defaultdict
from datetime import datetime

from ..models import (
    ContentTimeCorrelation,
    MonthlyTrend,
    TimePattern,
    WatchHistoryEntry,
    WatchingPhase,
)

# Time slot definitions
TIME_SLOTS = {
    "late_night": (0, 5, "00:00-05:00"),
    "morning": (5, 12, "05:00-12:00"),
    "afternoon": (12, 18, "12:00-18:00"),
    "evening": (18, 24, "18:00-24:00"),
}

# Phase naming based on dominant categories
PHASE_NAMES = {
    "music": "Music Exploration",
    "gaming": "Gaming Focus",
    "tech": "Tech Learning",
    "education": "Study Period",
    "entertainment": "Entertainment Binge",
    "general": "Mixed Viewing",
}


def analyze_time_patterns(entries: list[WatchHistoryEntry]) -> TimePattern:
    """
    Analyze viewing patterns by time of day and day of week.

    Args:
        entries: List of watch history entries

    Returns:
        TimePattern with peak hours, days, and ratios
    """
    if not entries:
        raise ValueError("No entries to analyze")

    hours = [e.time.hour for e in entries]
    days = [e.time.strftime("%A") for e in entries]  # Full day name

    hourly_dist = dict(Counter(hours))
    daily_dist = dict(Counter(days))

    # Find peak hours (top 3)
    peak_hours = [h for h, _ in Counter(hours).most_common(3)]

    # Find peak days (top 2)
    peak_days = [d for d, _ in Counter(days).most_common(2)]

    # Late night ratio (00:00 - 05:00)
    late_night_count = sum(1 for h in hours if 0 <= h < 5)
    late_night_ratio = late_night_count / len(entries) if entries else 0

    # Weekend ratio
    weekend_days = {"Saturday", "Sunday"}
    weekend_count = sum(1 for d in days if d in weekend_days)
    weekend_ratio = weekend_count / len(entries) if entries else 0

    return TimePattern(
        peak_hours=peak_hours,
        peak_days=peak_days,
        hourly_distribution=hourly_dist,
        daily_distribution=daily_dist,
        late_night_ratio=round(late_night_ratio, 3),
        weekend_ratio=round(weekend_ratio, 3),
    )


def analyze_monthly_trends(
    entries: list[WatchHistoryEntry],
    top_n: int = 3,
) -> list[MonthlyTrend]:
    """
    Analyze monthly viewing trends.

    Args:
        entries: List of watch history entries
        top_n: Number of top categories/channels per month

    Returns:
        List of MonthlyTrend objects sorted by month
    """
    from .topics import CATEGORY_KEYWORDS

    if not entries:
        return []

    # Group entries by month
    monthly_data: dict[str, list[WatchHistoryEntry]] = defaultdict(list)
    for entry in entries:
        month_key = entry.time.strftime("%Y-%m")
        monthly_data[month_key].append(entry)

    trends = []
    for month, month_entries in sorted(monthly_data.items()):
        # Count channels
        channels = [e.channel_name for e in month_entries if e.channel_name]
        top_channels = [ch for ch, _ in Counter(channels).most_common(top_n)]

        # Detect categories from titles
        titles = [e.clean_title.lower() for e in month_entries]
        category_counts: Counter = Counter()
        for title in titles:
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(kw in title for kw in keywords):
                    category_counts[category] += 1
        top_categories = [cat for cat, _ in category_counts.most_common(top_n)]

        # Calculate average daily videos
        days_in_month = len(set(e.time.date() for e in month_entries))
        avg_daily = len(month_entries) / max(days_in_month, 1)

        trends.append(MonthlyTrend(
            month=month,
            video_count=len(month_entries),
            top_categories=top_categories or ["general"],
            top_channels=top_channels,
            avg_daily_videos=round(avg_daily, 2),
        ))

    return trends


def analyze_content_by_time(
    entries: list[WatchHistoryEntry],
    top_n: int = 5,
) -> list[ContentTimeCorrelation]:
    """
    Analyze what content is watched at different times of day.

    Args:
        entries: List of watch history entries
        top_n: Number of top items per time slot

    Returns:
        List of ContentTimeCorrelation objects
    """
    from .topics import CATEGORY_KEYWORDS, extract_keywords_simple

    if not entries:
        return []

    # Group entries by time slot
    slot_entries: dict[str, list[WatchHistoryEntry]] = defaultdict(list)
    for entry in entries:
        hour = entry.time.hour
        for slot_name, (start, end, _) in TIME_SLOTS.items():
            if start <= hour < end:
                slot_entries[slot_name].append(entry)
                break

    correlations = []
    for slot_name, slot_data in slot_entries.items():
        if not slot_data:
            continue

        _, _, hour_range = TIME_SLOTS[slot_name]

        # Extract keywords from this time slot
        titles = [e.clean_title for e in slot_data]
        keywords = extract_keywords_simple(titles, limit=top_n)
        top_keywords = [kw for kw, _ in keywords]

        # Detect categories
        titles_lower = [t.lower() for t in titles]
        category_counts: Counter = Counter()
        for title in titles_lower:
            for category, cat_keywords in CATEGORY_KEYWORDS.items():
                if any(kw in title for kw in cat_keywords):
                    category_counts[category] += 1
        top_categories = [cat for cat, _ in category_counts.most_common(top_n)]

        correlations.append(ContentTimeCorrelation(
            time_slot=slot_name,
            hour_range=hour_range,
            top_categories=top_categories or ["general"],
            top_keywords=top_keywords,
            video_count=len(slot_data),
        ))

    return correlations


def detect_watching_phases(
    entries: list[WatchHistoryEntry],
    min_phase_days: int = 14,
) -> list[WatchingPhase]:
    """
    Detect distinct watching phases based on content pattern changes.

    Args:
        entries: List of watch history entries
        min_phase_days: Minimum days for a phase to be detected

    Returns:
        List of WatchingPhase objects
    """
    from .topics import CATEGORY_KEYWORDS

    if not entries:
        return []

    # Sort entries by time
    sorted_entries = sorted(entries, key=lambda e: e.time)

    # Group by week for phase detection
    weekly_data: dict[str, list[WatchHistoryEntry]] = defaultdict(list)
    for entry in sorted_entries:
        week_key = entry.time.strftime("%Y-W%W")
        weekly_data[week_key].append(entry)

    # Calculate dominant category per week
    weekly_categories: list[tuple[str, str, int]] = []  # (week, category, count)
    for week, week_entries in sorted(weekly_data.items()):
        titles = [e.clean_title.lower() for e in week_entries]
        category_counts: Counter = Counter()
        for title in titles:
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(kw in title for kw in keywords):
                    category_counts[category] += 1
        dominant = category_counts.most_common(1)
        cat = dominant[0][0] if dominant else "general"
        weekly_categories.append((week, cat, len(week_entries)))

    if not weekly_categories:
        return []

    # Detect phase changes (when dominant category changes)
    phases = []
    current_phase_start = weekly_categories[0][0]
    current_category = weekly_categories[0][1]
    phase_video_count = weekly_categories[0][2]
    phase_weeks = 1

    for i in range(1, len(weekly_categories)):
        week, cat, count = weekly_categories[i]
        if cat != current_category or i == len(weekly_categories) - 1:
            # Phase ended
            if phase_weeks >= 2:  # At least 2 weeks for a phase
                phase_name = PHASE_NAMES.get(current_category, "Mixed Viewing")
                start_date = datetime.strptime(current_phase_start + "-1", "%Y-W%W-%w")
                end_date = datetime.strptime(weekly_categories[i-1][0] + "-1", "%Y-W%W-%w")
                period = f"{start_date.strftime('%Y.%m')} - {end_date.strftime('%Y.%m')}"

                phases.append(WatchingPhase(
                    period=period,
                    phase_name=phase_name,
                    dominant_categories=[current_category],
                    video_count=phase_video_count,
                    description=f"{phase_weeks} weeks of {phase_name.lower()} ({phase_video_count} videos)",
                ))

            # Start new phase
            current_phase_start = week
            current_category = cat
            phase_video_count = count
            phase_weeks = 1
        else:
            phase_video_count += count
            phase_weeks += 1

    return phases
