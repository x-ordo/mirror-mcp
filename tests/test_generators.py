"""Tests for generators module."""

import pytest
from pathlib import Path

from mirror_mcp.parsers.youtube import parse_watch_history
from mirror_mcp.analyzers.topics import analyze_topics
from mirror_mcp.analyzers.time_patterns import analyze_time_patterns
from mirror_mcp.generators.suno_prompt import (
    build_taste_profile,
    generate_suno_prompt,
    generate_multiple_prompts,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_watch_history.json"


@pytest.fixture
def entries():
    """Load test entries fixture."""
    return parse_watch_history(str(FIXTURE_PATH))


@pytest.fixture
def taste_profile(entries):
    """Build taste profile from entries."""
    topics = analyze_topics(entries)
    patterns = analyze_time_patterns(entries)
    return build_taste_profile(topics, patterns)


class TestTasteProfile:
    """Tests for taste profile builder."""

    def test_build_taste_profile(self, entries):
        """Test taste profile building."""
        topics = analyze_topics(entries)
        patterns = analyze_time_patterns(entries)
        profile = build_taste_profile(topics, patterns)

        assert len(profile.primary_genres) > 0
        assert len(profile.mood_keywords) > 0
        assert profile.energy_level in ["low", "medium", "high"]
        assert profile.tempo_preference in ["slow", "moderate", "fast"]
        assert profile.language_preference in ["korean", "english", "mixed"]


class TestSunoPrompt:
    """Tests for Suno prompt generator."""

    def test_generate_suno_prompt(self, taste_profile):
        """Test single prompt generation."""
        prompt = generate_suno_prompt(taste_profile)

        assert len(prompt.full_prompt) <= 200  # Suno limit
        assert prompt.style_tags
        assert prompt.mood
        assert prompt.tempo_bpm
        assert prompt.instruments

    def test_generate_multiple_prompts(self, taste_profile):
        """Test multiple prompt generation."""
        prompts = generate_multiple_prompts(taste_profile, count=3)

        assert len(prompts) == 3
        # All prompts should be different
        full_prompts = [p.full_prompt for p in prompts]
        assert len(set(full_prompts)) > 1  # At least some variation

    def test_generate_multiple_prompts_limit(self, taste_profile):
        """Test prompt count limits."""
        # Should clamp to 1-5
        prompts_min = generate_multiple_prompts(taste_profile, count=0)
        assert len(prompts_min) == 1

        prompts_max = generate_multiple_prompts(taste_profile, count=10)
        assert len(prompts_max) == 5

    def test_prompt_length_limit(self, taste_profile):
        """Test all prompts respect 200 char limit."""
        prompts = generate_multiple_prompts(taste_profile, count=5)

        for prompt in prompts:
            assert len(prompt.full_prompt) <= 200, f"Prompt too long: {len(prompt.full_prompt)}"
