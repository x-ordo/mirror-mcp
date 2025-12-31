"""Watch history statistics analyzer."""

import math
from collections import Counter

from ..models import DiversityScore, WatchHistoryEntry, WatchStatistics


def analyze_watch_statistics(entries: list[WatchHistoryEntry]) -> WatchStatistics:
    """
    Generate overall statistics from watch history.

    Args:
        entries: List of watch history entries

    Returns:
        WatchStatistics with aggregated data
    """
    if not entries:
        raise ValueError("No entries to analyze")

    # Channel frequency
    channels = [e.channel_name for e in entries if e.channel_name]
    channel_counts = Counter(channels).most_common(20)

    # Date range
    timestamps = [e.time for e in entries]
    date_start = min(timestamps)
    date_end = max(timestamps)

    # Daily average
    days_span = (date_end - date_start).days or 1
    videos_per_day = len(entries) / days_span

    return WatchStatistics(
        total_videos=len(entries),
        unique_channels=len(set(channels)),
        date_range_start=date_start,
        date_range_end=date_end,
        top_channels=channel_counts,
        videos_per_day_avg=round(videos_per_day, 2),
    )


def calculate_diversity_score(entries: list[WatchHistoryEntry]) -> DiversityScore:
    """
    Calculate channel diversity metrics.

    Uses Shannon entropy to measure how diverse the viewing is.
    Higher scores mean more diverse viewing habits.

    Args:
        entries: List of watch history entries

    Returns:
        DiversityScore with entropy-based metrics
    """
    if not entries:
        return DiversityScore(
            overall_score=0,
            channel_entropy=0,
            top_channel_concentration=0,
            unique_ratio=0,
            interpretation="No data to analyze",
        )

    # Count videos per channel
    channels = [e.channel_name for e in entries if e.channel_name]
    if not channels:
        return DiversityScore(
            overall_score=0,
            channel_entropy=0,
            top_channel_concentration=0,
            unique_ratio=0,
            interpretation="No channel data available",
        )

    channel_counts = Counter(channels)
    total = len(channels)
    unique_channels = len(channel_counts)

    # Calculate Shannon entropy
    entropy = 0.0
    for count in channel_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    # Maximum possible entropy (if all videos were from different channels)
    max_entropy = math.log2(total) if total > 1 else 1

    # Normalize entropy to 0-100 scale
    normalized_entropy = (entropy / max_entropy * 100) if max_entropy > 0 else 0

    # Top 5 channel concentration
    top_5_counts = sum(count for _, count in channel_counts.most_common(5))
    top_concentration = (top_5_counts / total * 100) if total > 0 else 0

    # Unique ratio
    unique_ratio = (unique_channels / total) if total > 0 else 0

    # Calculate overall score (weighted combination)
    # Lower concentration + higher entropy = higher score
    overall_score = (normalized_entropy * 0.5 + (100 - top_concentration) * 0.3 + unique_ratio * 100 * 0.2)
    overall_score = min(100, max(0, overall_score))

    # Generate interpretation
    if overall_score >= 70:
        interpretation = "Highly diverse - you explore many different channels"
    elif overall_score >= 50:
        interpretation = "Moderately diverse - you have favorites but still explore"
    elif overall_score >= 30:
        interpretation = "Focused viewer - you stick to your preferred channels"
    else:
        interpretation = "Very focused - you primarily watch a few channels"

    return DiversityScore(
        overall_score=round(overall_score, 1),
        channel_entropy=round(entropy, 3),
        top_channel_concentration=round(top_concentration, 1),
        unique_ratio=round(unique_ratio, 3),
        interpretation=interpretation,
    )
