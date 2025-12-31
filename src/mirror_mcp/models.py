"""Data models for Mirror MCP."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChannelInfo(BaseModel):
    """YouTube channel information from subtitles field."""

    name: str
    url: Optional[str] = None


class WatchHistoryEntry(BaseModel):
    """Single entry from Google Takeout watch-history.json."""

    header: str = "YouTube"
    title: str
    titleUrl: Optional[str] = None
    subtitles: list[ChannelInfo] = Field(default_factory=list)
    time: datetime
    products: list[str] = Field(default_factory=lambda: ["YouTube"])
    activityControls: list[str] = Field(default_factory=list)

    @property
    def video_id(self) -> Optional[str]:
        """Extract video ID from titleUrl."""
        if self.titleUrl and "watch?v=" in self.titleUrl:
            return self.titleUrl.split("watch?v=")[-1].split("&")[0]
        return None

    @property
    def clean_title(self) -> str:
        """Remove 'Watched ' prefix from title."""
        return self.title.removeprefix("Watched ")

    @property
    def channel_name(self) -> Optional[str]:
        """Get channel name if available."""
        return self.subtitles[0].name if self.subtitles else None


class WatchStatistics(BaseModel):
    """Overall watch history statistics."""

    total_videos: int
    unique_channels: int
    date_range_start: datetime
    date_range_end: datetime
    top_channels: list[tuple[str, int]]
    videos_per_day_avg: float


class TopicAnalysis(BaseModel):
    """Keyword/topic extraction results."""

    keywords: list[tuple[str, int]]
    language_breakdown: dict[str, int]
    categories: list[str]


class TimePattern(BaseModel):
    """Time-based viewing patterns."""

    peak_hours: list[int]
    peak_days: list[str]
    hourly_distribution: dict[int, int]
    daily_distribution: dict[str, int]
    late_night_ratio: float
    weekend_ratio: float


class TasteProfile(BaseModel):
    """Combined taste profile for prompt generation."""

    primary_genres: list[str]
    mood_keywords: list[str]
    energy_level: str
    tempo_preference: str
    time_context: str
    language_preference: str


class SunoPrompt(BaseModel):
    """Generated Suno music prompt."""

    style_tags: str
    mood: str
    tempo_bpm: str
    instruments: str
    full_prompt: str


class MonthlyTrend(BaseModel):
    """Monthly viewing trend data."""

    month: str  # YYYY-MM format
    video_count: int
    top_categories: list[str]
    top_channels: list[str]
    avg_daily_videos: float


class ContentTimeCorrelation(BaseModel):
    """Content-time correlation analysis."""

    time_slot: str  # e.g., "late_night", "morning"
    hour_range: str  # e.g., "00:00-05:00"
    top_categories: list[str]
    top_keywords: list[str]
    video_count: int


class WatchingPhase(BaseModel):
    """Detected watching phase/period."""

    period: str  # e.g., "2024.06 - 2024.08"
    phase_name: str  # e.g., "Gaming Focus", "Music Exploration"
    dominant_categories: list[str]
    video_count: int
    description: str


class DiversityScore(BaseModel):
    """Channel diversity metrics."""

    overall_score: float  # 0-100
    channel_entropy: float
    top_channel_concentration: float  # % of videos from top 5 channels
    unique_ratio: float  # unique channels / total videos
    interpretation: str
