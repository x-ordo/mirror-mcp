"""Mirror MCP Server - YouTube watch history analyzer and Suno prompt generator."""

import json
from collections import Counter
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .analyzers.statistics import analyze_watch_statistics, calculate_diversity_score
from .analyzers.time_patterns import (
    analyze_content_by_time,
    analyze_monthly_trends,
    analyze_time_patterns,
    detect_watching_phases,
)
from .analyzers.topics import analyze_topics
from .generators.suno_prompt import (
    build_taste_profile,
    generate_multiple_prompts,
    generate_suno_prompt,
)
from .models import WatchHistoryEntry
from .parsers.youtube import parse_watch_history

# Initialize FastMCP server
mcp = FastMCP(
    "Mirror MCP",
    dependencies=[
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
    ],
)

# Cache file path
CACHE_FILE = Path.home() / ".mirror_mcp_cache.json"

# In-memory state to store parsed data between tool calls
_state: dict = {
    "entries": None,
    "file_path": None,
    "analysis_cache": {},
}


def _save_cache() -> bool:
    """Save current analysis state to cache file."""
    if _state["entries"] is None:
        return False

    try:
        cache_data = {
            "file_path": _state["file_path"],
            "entries": [
                {
                    "title": e.title,
                    "titleUrl": e.titleUrl,
                    "time": e.time.isoformat(),
                    "subtitles": [{"name": s.name, "url": s.url} for s in e.subtitles],
                }
                for e in _state["entries"]
            ],
        }
        CACHE_FILE.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2))
        return True
    except Exception:
        return False


def _load_cache() -> bool:
    """Load analysis state from cache file."""
    if not CACHE_FILE.exists():
        return False

    try:
        cache_data = json.loads(CACHE_FILE.read_text())
        entries = []
        for e in cache_data["entries"]:
            from .models import ChannelInfo
            entry = WatchHistoryEntry(
                title=e["title"],
                titleUrl=e.get("titleUrl"),
                time=e["time"],
                subtitles=[ChannelInfo(**s) for s in e.get("subtitles", [])],
            )
            entries.append(entry)
        _state["entries"] = entries
        _state["file_path"] = cache_data.get("file_path")
        return True
    except Exception:
        return False


def _clear_cache() -> bool:
    """Clear the cache file."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        return True
    except Exception:
        return False


@mcp.tool()
def analyze_watch_history(file_path: str) -> dict:
    """
    Parse YouTube watch-history.json from Google Takeout and extract statistics.

    Args:
        file_path: Path to the watch-history.json file

    Returns:
        Dictionary containing total videos, unique channels, date range, and top channels
    """
    entries = parse_watch_history(file_path)
    _state["entries"] = entries
    _state["file_path"] = file_path

    # Save to cache for persistence
    _save_cache()

    stats = analyze_watch_statistics(entries)

    return {
        "total_videos": stats.total_videos,
        "unique_channels": stats.unique_channels,
        "date_range": f"{stats.date_range_start.date()} to {stats.date_range_end.date()}",
        "top_channels": [
            {"channel": ch, "count": cnt} for ch, cnt in stats.top_channels[:10]
        ],
        "videos_per_day_avg": stats.videos_per_day_avg,
        "message": f"Analyzed {stats.total_videos} videos from {stats.unique_channels} channels",
    }


@mcp.tool()
def load_cached_data() -> dict:
    """
    Load previously analyzed watch history from cache.
    Use this to restore data after server restart.

    Returns:
        Dictionary containing cache status and loaded data summary
    """
    if _load_cache():
        stats = analyze_watch_statistics(_state["entries"])
        return {
            "status": "loaded",
            "file_path": _state["file_path"],
            "total_videos": stats.total_videos,
            "unique_channels": stats.unique_channels,
            "message": f"Loaded {stats.total_videos} videos from cache",
        }
    return {
        "status": "no_cache",
        "message": "No cached data found. Please run analyze_watch_history first.",
    }


@mcp.tool()
def clear_cache() -> dict:
    """
    Clear the cached watch history data.

    Returns:
        Dictionary containing clear status
    """
    if _clear_cache():
        _state["entries"] = None
        _state["file_path"] = None
        return {"status": "cleared", "message": "Cache cleared successfully"}
    return {"status": "error", "message": "Failed to clear cache"}


@mcp.tool()
def get_top_topics(limit: int = 20) -> dict:
    """
    Extract top keywords from video titles in watch history.
    Must call analyze_watch_history first.

    Args:
        limit: Maximum number of keywords to return (default: 20)

    Returns:
        Dictionary containing top keywords, language breakdown, and inferred categories
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    topic_analysis = analyze_topics(_state["entries"], limit=limit)

    return {
        "keywords": [{"word": k, "count": c} for k, c in topic_analysis.keywords],
        "language_breakdown": topic_analysis.language_breakdown,
        "categories": topic_analysis.categories,
        "message": f"Extracted {len(topic_analysis.keywords)} keywords",
    }


@mcp.tool()
def get_time_patterns() -> dict:
    """
    Analyze viewing patterns by time of day and day of week.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing peak hours, peak days, late night ratio, and weekend ratio
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    patterns = analyze_time_patterns(_state["entries"])

    # Generate insight
    insights = []
    if patterns.late_night_ratio > 0.3:
        insights.append(
            "You're a night owl - 30%+ of videos watched between midnight and 5am"
        )
    if patterns.weekend_ratio > 0.5:
        insights.append("Weekend watcher - majority of viewing happens on weekends")
    if patterns.peak_hours:
        insights.append(f"Peak viewing hours: {patterns.peak_hours}")
    insight = " | ".join(insights) if insights else "Balanced viewing patterns"

    return {
        "peak_hours": patterns.peak_hours,
        "peak_days": patterns.peak_days,
        "late_night_ratio": patterns.late_night_ratio,
        "weekend_ratio": patterns.weekend_ratio,
        "hourly_distribution": patterns.hourly_distribution,
        "insight": insight,
    }


@mcp.tool()
def generate_music_prompt() -> dict:
    """
    Generate a Suno AI music prompt based on analyzed taste profile.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing style tags, mood, tempo, instruments, and full Suno prompt
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    # Run required analyses
    topic_analysis = analyze_topics(_state["entries"])
    time_patterns = analyze_time_patterns(_state["entries"])

    # Build taste profile and generate prompt
    taste_profile = build_taste_profile(topic_analysis, time_patterns)
    suno_prompt = generate_suno_prompt(taste_profile)

    return {
        "taste_profile": {
            "primary_genres": taste_profile.primary_genres,
            "mood_keywords": taste_profile.mood_keywords,
            "energy_level": taste_profile.energy_level,
            "time_context": taste_profile.time_context,
            "language_preference": taste_profile.language_preference,
        },
        "suno_prompt": {
            "style": suno_prompt.style_tags,
            "mood": suno_prompt.mood,
            "tempo": suno_prompt.tempo_bpm,
            "instruments": suno_prompt.instruments,
            "full_prompt": suno_prompt.full_prompt,
        },
        "message": f"Generated Suno prompt: {suno_prompt.full_prompt}",
    }


@mcp.tool()
def get_channel_stats(channel_name: str) -> dict:
    """
    Get detailed statistics for a specific channel.
    Must call analyze_watch_history first.

    Args:
        channel_name: Name of the channel to analyze

    Returns:
        Dictionary containing video count, time patterns, and viewing period for the channel
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    # Filter entries for this channel
    channel_entries = [
        e for e in _state["entries"]
        if e.channel_name and channel_name.lower() in e.channel_name.lower()
    ]

    if not channel_entries:
        return {"error": f"No videos found for channel: {channel_name}"}

    # Get timestamps
    timestamps = [e.time for e in channel_entries]
    first_watch = min(timestamps)
    last_watch = max(timestamps)

    # Hourly distribution
    hours = [e.time.hour for e in channel_entries]
    hourly_dist = dict(Counter(hours))
    peak_hours = [h for h, _ in Counter(hours).most_common(3)]

    # Day of week distribution
    days = [e.time.strftime("%A") for e in channel_entries]
    daily_dist = dict(Counter(days))
    peak_days = [d for d, _ in Counter(days).most_common(2)]

    return {
        "channel": channel_entries[0].channel_name,
        "total_videos": len(channel_entries),
        "first_watched": first_watch.isoformat(),
        "last_watched": last_watch.isoformat(),
        "viewing_period_days": (last_watch - first_watch).days,
        "peak_hours": peak_hours,
        "peak_days": peak_days,
        "hourly_distribution": hourly_dist,
        "daily_distribution": daily_dist,
        "message": f"Found {len(channel_entries)} videos from {channel_entries[0].channel_name}",
    }


@mcp.tool()
def get_monthly_trends() -> dict:
    """
    Analyze monthly viewing trends over time.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing monthly video counts, top categories, and trend analysis
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    trends = analyze_monthly_trends(_state["entries"])

    # Calculate growth trend
    if len(trends) >= 2:
        first_half = sum(t.video_count for t in trends[: len(trends) // 2])
        second_half = sum(t.video_count for t in trends[len(trends) // 2 :])
        if first_half > 0:
            growth = ((second_half - first_half) / first_half) * 100
            trend_label = "increasing" if growth > 10 else "decreasing" if growth < -10 else "stable"
        else:
            growth = 0
            trend_label = "stable"
    else:
        growth = 0
        trend_label = "insufficient data"

    return {
        "months": [
            {
                "month": t.month,
                "video_count": t.video_count,
                "top_categories": t.top_categories,
                "top_channels": t.top_channels,
                "avg_daily": t.avg_daily_videos,
            }
            for t in trends
        ],
        "total_months": len(trends),
        "trend": trend_label,
        "growth_percent": round(growth, 1),
        "message": f"Analyzed {len(trends)} months of viewing history. Trend: {trend_label}",
    }


@mcp.tool()
def get_content_by_time() -> dict:
    """
    Analyze what content is watched at different times of day.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing content breakdown by time slot (late night, morning, afternoon, evening)
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    correlations = analyze_content_by_time(_state["entries"])

    return {
        "time_slots": [
            {
                "slot": c.time_slot,
                "hours": c.hour_range,
                "video_count": c.video_count,
                "top_categories": c.top_categories,
                "top_keywords": c.top_keywords,
            }
            for c in correlations
        ],
        "insights": _generate_time_insights(correlations),
        "message": f"Analyzed content patterns across {len(correlations)} time slots",
    }


def _generate_time_insights(correlations) -> list:
    """Generate human-readable insights from time correlations."""
    insights = []
    for c in correlations:
        if c.video_count > 0:
            top_cat = c.top_categories[0] if c.top_categories else "general"
            insights.append(f"{c.time_slot.replace('_', ' ').title()}: primarily {top_cat} content")
    return insights


@mcp.tool()
def generate_music_prompts(count: int = 3) -> dict:
    """
    Generate multiple varied Suno AI music prompts based on taste profile.
    Must call analyze_watch_history first.

    Args:
        count: Number of prompts to generate (1-5, default: 3)

    Returns:
        Dictionary containing multiple Suno prompts with different styles
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    # Run required analyses
    topic_analysis = analyze_topics(_state["entries"])
    time_patterns = analyze_time_patterns(_state["entries"])

    # Build taste profile and generate prompts
    taste_profile = build_taste_profile(topic_analysis, time_patterns)
    prompts = generate_multiple_prompts(taste_profile, count)

    labels = ["Main Style", "Energy Variation", "Mood Variation", "Instrument Variation", "Genre Fusion"]

    return {
        "prompts": [
            {
                "label": labels[i] if i < len(labels) else f"Variation {i+1}",
                "style": p.style_tags,
                "mood": p.mood,
                "tempo": p.tempo_bpm,
                "instruments": p.instruments,
                "full_prompt": p.full_prompt,
            }
            for i, p in enumerate(prompts)
        ],
        "count": len(prompts),
        "message": f"Generated {len(prompts)} Suno prompt variations",
    }


@mcp.tool()
def detect_phases() -> dict:
    """
    Detect distinct watching phases based on content pattern changes.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing detected viewing phases with their characteristics
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    phases = detect_watching_phases(_state["entries"])

    return {
        "phases": [
            {
                "period": p.period,
                "name": p.phase_name,
                "categories": p.dominant_categories,
                "video_count": p.video_count,
                "description": p.description,
            }
            for p in phases
        ],
        "total_phases": len(phases),
        "message": f"Detected {len(phases)} distinct viewing phases",
    }


@mcp.tool()
def get_diversity_score() -> dict:
    """
    Calculate channel diversity metrics based on viewing history.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing diversity score, entropy, and concentration metrics
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    score = calculate_diversity_score(_state["entries"])

    return {
        "overall_score": score.overall_score,
        "channel_entropy": score.channel_entropy,
        "top_channel_concentration": score.top_channel_concentration,
        "unique_ratio": score.unique_ratio,
        "interpretation": score.interpretation,
        "message": f"Diversity score: {score.overall_score}/100 - {score.interpretation}",
    }


@mcp.tool()
def export_analysis(format: str = "markdown") -> dict:
    """
    Export complete analysis results in specified format.
    Must call analyze_watch_history first.

    Args:
        format: Output format - 'markdown' or 'json' (default: markdown)

    Returns:
        Dictionary containing formatted analysis report
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    # Run all analyses
    stats = analyze_watch_statistics(_state["entries"])
    topics = analyze_topics(_state["entries"])
    patterns = analyze_time_patterns(_state["entries"])
    diversity = calculate_diversity_score(_state["entries"])

    if format.lower() == "json":
        return {
            "format": "json",
            "content": {
                "statistics": {
                    "total_videos": stats.total_videos,
                    "unique_channels": stats.unique_channels,
                    "date_range": f"{stats.date_range_start.date()} to {stats.date_range_end.date()}",
                    "videos_per_day_avg": stats.videos_per_day_avg,
                },
                "topics": {
                    "keywords": [{"word": k, "count": c} for k, c in topics.keywords[:10]],
                    "categories": topics.categories,
                },
                "time_patterns": {
                    "peak_hours": patterns.peak_hours,
                    "peak_days": patterns.peak_days,
                    "late_night_ratio": patterns.late_night_ratio,
                    "weekend_ratio": patterns.weekend_ratio,
                },
                "diversity": {
                    "score": diversity.overall_score,
                    "interpretation": diversity.interpretation,
                },
            },
            "message": "Exported analysis in JSON format",
        }
    else:
        # Markdown format
        md = f"""# YouTube Watch History Analysis Report

## Overview
- **Total Videos**: {stats.total_videos}
- **Unique Channels**: {stats.unique_channels}
- **Date Range**: {stats.date_range_start.date()} to {stats.date_range_end.date()}
- **Average Videos/Day**: {stats.videos_per_day_avg}

## Top Keywords
{_format_keywords_md(topics.keywords[:10])}

## Categories
{', '.join(topics.categories)}

## Viewing Patterns
- **Peak Hours**: {', '.join(str(h) + ':00' for h in patterns.peak_hours)}
- **Peak Days**: {', '.join(patterns.peak_days)}
- **Late Night Ratio**: {patterns.late_night_ratio:.1%}
- **Weekend Ratio**: {patterns.weekend_ratio:.1%}

## Channel Diversity
- **Score**: {diversity.overall_score}/100
- **Interpretation**: {diversity.interpretation}

---
*Generated by Mirror MCP*
"""
        return {
            "format": "markdown",
            "content": md,
            "message": "Exported analysis in Markdown format",
        }


def _format_keywords_md(keywords: list) -> str:
    """Format keywords as markdown list."""
    return "\n".join(f"- {word}: {count}" for word, count in keywords)


@mcp.tool()
def suggest_content() -> dict:
    """
    Suggest content based on taste profile analysis.
    Must call analyze_watch_history first.

    Returns:
        Dictionary containing content suggestions based on viewing patterns
    """
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first to load data"}

    topics = analyze_topics(_state["entries"])
    patterns = analyze_time_patterns(_state["entries"])
    taste = build_taste_profile(topics, patterns)

    # Get current top channels
    channels = [e.channel_name for e in _state["entries"] if e.channel_name]
    top_channels = [ch for ch, _ in Counter(channels).most_common(5)]

    # Generate suggestions based on categories and genres
    suggestions = {
        "based_on_genres": _suggest_by_genre(taste.primary_genres),
        "explore_new": _suggest_exploration(topics.categories),
        "time_based": _suggest_by_time(patterns),
    }

    return {
        "current_favorites": top_channels,
        "primary_genres": taste.primary_genres,
        "suggestions": suggestions,
        "message": "Generated content suggestions based on your viewing history",
    }


def _suggest_by_genre(genres: list) -> list:
    """Suggest content based on detected genres."""
    genre_suggestions = {
        "Lo-fi": ["Study playlists", "Ambient music channels", "Chill hop compilations"],
        "Jazz": ["Smooth jazz collections", "Live jazz performances", "Jazz cafe playlists"],
        "K-pop": ["K-pop dance practices", "Behind-the-scenes content", "Music show stages"],
        "Hip-hop": ["Freestyle sessions", "Producer tutorials", "Hip-hop documentaries"],
        "Pop": ["Pop music charts", "Artist interviews", "Music video reactions"],
        "Indie": ["Indie artist spotlights", "Acoustic sessions", "Indie music festivals"],
        "EDM": ["DJ sets", "Festival recordings", "Electronic music tutorials"],
        "Rock": ["Live concert recordings", "Guitar tutorials", "Rock documentaries"],
    }

    suggestions = []
    for genre in genres[:3]:
        if genre in genre_suggestions:
            suggestions.extend(genre_suggestions[genre][:2])
    return suggestions or ["Explore trending music", "New artist discoveries"]


def _suggest_exploration(categories: list) -> list:
    """Suggest new categories to explore."""
    exploration_map = {
        "music": ["Podcasts about music", "Music production tutorials", "Artist documentaries"],
        "gaming": ["Game development streams", "Esports tournaments", "Gaming podcasts"],
        "tech": ["Science channels", "DIY electronics", "Future tech documentaries"],
        "education": ["Language learning", "Skill-building courses", "Documentary channels"],
        "entertainment": ["Stand-up comedy", "Film analysis", "Behind-the-scenes content"],
    }

    current = set(categories)
    suggestions = []
    for cat, items in exploration_map.items():
        if cat not in current:
            suggestions.extend(items[:1])
    return suggestions[:5] or ["Explore new content categories"]


def _suggest_by_time(patterns) -> dict:
    """Suggest content based on viewing time patterns."""
    suggestions = {}

    if patterns.late_night_ratio > 0.3:
        suggestions["late_night"] = ["Relaxing content", "ASMR", "Ambient music", "Meditation guides"]

    if patterns.weekend_ratio > 0.5:
        suggestions["weekend"] = ["Long-form documentaries", "Movie reviews", "Binge-worthy series"]

    if any(h < 10 for h in patterns.peak_hours):
        suggestions["morning"] = ["News summaries", "Motivation content", "Quick tutorials"]

    return suggestions or {"general": ["Curated playlists based on your preferences"]}


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
