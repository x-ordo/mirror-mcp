"""Tests for analyzers module."""

import pytest
from pathlib import Path

from mirror_mcp.parsers.youtube import parse_watch_history
from mirror_mcp.analyzers.statistics import analyze_watch_statistics, calculate_diversity_score
from mirror_mcp.analyzers.topics import (
    analyze_topics,
    normalize_keyword,
    extract_keywords_simple,
)
from mirror_mcp.analyzers.time_patterns import (
    analyze_time_patterns,
    analyze_monthly_trends,
    analyze_content_by_time,
    detect_watching_phases,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_watch_history.json"


@pytest.fixture
def entries():
    """Load test entries fixture."""
    return parse_watch_history(str(FIXTURE_PATH))


class TestStatistics:
    """Tests for statistics analyzer."""

    def test_analyze_watch_statistics(self, entries):
        """Test basic statistics calculation."""
        stats = analyze_watch_statistics(entries)

        assert stats.total_videos == 5
        assert stats.unique_channels == 5
        assert stats.videos_per_day_avg > 0

    def test_analyze_watch_statistics_empty(self):
        """Test handling of empty entries."""
        with pytest.raises(ValueError):
            analyze_watch_statistics([])

    def test_calculate_diversity_score(self, entries):
        """Test diversity score calculation."""
        score = calculate_diversity_score(entries)

        assert 0 <= score.overall_score <= 100
        assert score.channel_entropy >= 0
        assert 0 <= score.top_channel_concentration <= 100
        assert score.interpretation != ""


class TestTopics:
    """Tests for topics analyzer."""

    def test_normalize_keyword_synonyms(self):
        """Test keyword synonym normalization."""
        assert normalize_keyword("k-pop") == "kpop"
        assert normalize_keyword("케이팝") == "kpop"
        assert normalize_keyword("K-POP") == "kpop"

        assert normalize_keyword("lo-fi") == "lofi"
        assert normalize_keyword("로파이") == "lofi"

        assert normalize_keyword("hip-hop") == "hiphop"
        assert normalize_keyword("힙합") == "hiphop"

    def test_normalize_keyword_unknown(self):
        """Test normalization of unknown keywords."""
        assert normalize_keyword("unknown") == "unknown"
        assert normalize_keyword("UPPER") == "upper"

    def test_extract_keywords_simple(self):
        """Test simple keyword extraction."""
        titles = ["Lo-fi beats to study", "Jazz piano music", "K-pop hits 2024"]
        keywords = extract_keywords_simple(titles, limit=10)

        assert len(keywords) > 0
        # Keywords should be normalized
        keyword_words = [k for k, _ in keywords]
        assert "lofi" in keyword_words or "jazz" in keyword_words

    def test_analyze_topics(self, entries):
        """Test full topic analysis."""
        analysis = analyze_topics(entries)

        assert len(analysis.keywords) > 0
        assert "music" in analysis.categories
        assert "korean" in analysis.language_breakdown
        assert "english" in analysis.language_breakdown


class TestTimePatterns:
    """Tests for time patterns analyzer."""

    def test_analyze_time_patterns(self, entries):
        """Test time pattern analysis."""
        patterns = analyze_time_patterns(entries)

        assert len(patterns.peak_hours) <= 3
        assert len(patterns.peak_days) <= 2
        assert 0 <= patterns.late_night_ratio <= 1
        assert 0 <= patterns.weekend_ratio <= 1

    def test_analyze_time_patterns_empty(self):
        """Test handling of empty entries."""
        with pytest.raises(ValueError):
            analyze_time_patterns([])

    def test_analyze_monthly_trends(self, entries):
        """Test monthly trend analysis."""
        trends = analyze_monthly_trends(entries)

        assert len(trends) >= 1
        for trend in trends:
            assert trend.video_count > 0
            assert trend.month  # YYYY-MM format

    def test_analyze_content_by_time(self, entries):
        """Test content-by-time analysis."""
        correlations = analyze_content_by_time(entries)

        assert len(correlations) > 0
        for corr in correlations:
            assert corr.time_slot in ["late_night", "morning", "afternoon", "evening"]
            assert corr.video_count >= 0

    def test_detect_watching_phases(self, entries):
        """Test phase detection (may return empty for small dataset)."""
        phases = detect_watching_phases(entries)

        # Small dataset may not have distinct phases
        assert isinstance(phases, list)
