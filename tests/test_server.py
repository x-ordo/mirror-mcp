"""Tests for MCP server tools."""

import pytest
from pathlib import Path

from mirror_mcp.server import (
    analyze_watch_history,
    get_top_topics,
    get_time_patterns,
    generate_music_prompt,
    get_channel_stats,
    get_monthly_trends,
    get_content_by_time,
    generate_music_prompts,
    detect_phases,
    get_diversity_score,
    export_analysis,
    suggest_content,
    load_cached_data,
    clear_cache,
    _state,
)


FIXTURE_PATH = str(Path(__file__).parent / "fixtures" / "sample_watch_history.json")


@pytest.fixture(autouse=True)
def reset_state():
    """Reset server state before each test."""
    _state["entries"] = None
    _state["file_path"] = None
    _state["analysis_cache"] = {}
    yield
    # Cleanup cache after test
    clear_cache()


class TestCoreTools:
    """Tests for core analysis tools."""

    def test_analyze_watch_history(self):
        """Test watch history analysis."""
        result = analyze_watch_history(FIXTURE_PATH)

        assert "error" not in result
        assert result["total_videos"] == 5
        assert result["unique_channels"] == 5

    def test_get_top_topics_without_data(self):
        """Test get_top_topics without loading data first."""
        result = get_top_topics()

        assert "error" in result

    def test_get_top_topics(self):
        """Test topic extraction."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_top_topics(limit=10)

        assert "error" not in result
        assert len(result["keywords"]) <= 10

    def test_get_time_patterns(self):
        """Test time pattern analysis."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_time_patterns()

        assert "error" not in result
        assert "peak_hours" in result
        assert "late_night_ratio" in result

    def test_generate_music_prompt(self):
        """Test music prompt generation."""
        analyze_watch_history(FIXTURE_PATH)
        result = generate_music_prompt()

        assert "error" not in result
        assert "suno_prompt" in result
        assert len(result["suno_prompt"]["full_prompt"]) <= 200


class TestAdvancedTools:
    """Tests for advanced analysis tools."""

    def test_get_channel_stats(self):
        """Test channel-specific stats."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_channel_stats("Lofi")

        assert "error" not in result
        assert result["total_videos"] >= 1

    def test_get_channel_stats_not_found(self):
        """Test channel stats for non-existent channel."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_channel_stats("NonExistentChannel12345")

        assert "error" in result

    def test_get_monthly_trends(self):
        """Test monthly trend analysis."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_monthly_trends()

        assert "error" not in result
        assert "months" in result
        assert "trend" in result

    def test_get_content_by_time(self):
        """Test content-by-time analysis."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_content_by_time()

        assert "error" not in result
        assert "time_slots" in result

    def test_detect_phases(self):
        """Test phase detection."""
        analyze_watch_history(FIXTURE_PATH)
        result = detect_phases()

        assert "error" not in result
        assert "phases" in result

    def test_get_diversity_score(self):
        """Test diversity score calculation."""
        analyze_watch_history(FIXTURE_PATH)
        result = get_diversity_score()

        assert "error" not in result
        assert 0 <= result["overall_score"] <= 100


class TestGenerationTools:
    """Tests for generation and export tools."""

    def test_generate_music_prompts_multiple(self):
        """Test multiple prompt generation."""
        analyze_watch_history(FIXTURE_PATH)
        result = generate_music_prompts(count=3)

        assert "error" not in result
        assert result["count"] == 3
        assert len(result["prompts"]) == 3

    def test_suggest_content(self):
        """Test content suggestions."""
        analyze_watch_history(FIXTURE_PATH)
        result = suggest_content()

        assert "error" not in result
        assert "suggestions" in result
        assert "current_favorites" in result

    def test_export_analysis_markdown(self):
        """Test markdown export."""
        analyze_watch_history(FIXTURE_PATH)
        result = export_analysis(format="markdown")

        assert "error" not in result
        assert result["format"] == "markdown"
        assert "# YouTube Watch History" in result["content"]

    def test_export_analysis_json(self):
        """Test JSON export."""
        analyze_watch_history(FIXTURE_PATH)
        result = export_analysis(format="json")

        assert "error" not in result
        assert result["format"] == "json"
        assert "statistics" in result["content"]


class TestCachingTools:
    """Tests for caching functionality."""

    def test_cache_save_load_cycle(self):
        """Test full cache save/load cycle."""
        # Load and cache data
        analyze_watch_history(FIXTURE_PATH)
        original_count = len(_state["entries"])

        # Clear in-memory state
        _state["entries"] = None
        _state["file_path"] = None

        # Load from cache
        result = load_cached_data()

        assert result["status"] == "loaded"
        assert len(_state["entries"]) == original_count

    def test_load_cached_data_no_cache(self):
        """Test loading when no cache exists."""
        clear_cache()
        result = load_cached_data()

        assert result["status"] == "no_cache"

    def test_clear_cache(self):
        """Test cache clearing."""
        analyze_watch_history(FIXTURE_PATH)
        result = clear_cache()

        assert result["status"] == "cleared"
        assert _state["entries"] is None
