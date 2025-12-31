# API Reference

Mirror MCP provides 14 tools for YouTube watch history analysis.

## Core Analysis Tools

### `analyze_watch_history`

Parse YouTube watch-history.json and extract statistics.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_path` | string | Yes | Path to watch-history.json file |

**Returns:**
```json
{
  "total_videos": 1234,
  "unique_channels": 89,
  "date_range": "2024-01-01 to 2024-12-31",
  "top_channels": [
    {"channel": "Lofi Girl", "count": 156}
  ],
  "videos_per_day_avg": 3.4,
  "message": "Analyzed 1234 videos from 89 channels"
}
```

---

### `get_top_topics`

Extract keywords from video titles with synonym normalization.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Max keywords to return |

**Returns:**
```json
{
  "keywords": [
    {"word": "lofi", "count": 89},
    {"word": "jazz", "count": 45}
  ],
  "language_breakdown": {"korean": 234, "english": 456},
  "categories": ["music", "entertainment"],
  "message": "Extracted 20 keywords"
}
```

**Synonym Normalization:**
- `k-pop`, `케이팝`, `kpop` → `kpop`
- `lo-fi`, `로파이`, `lofi` → `lofi`
- `hip-hop`, `힙합`, `hiphop` → `hiphop`

---

### `get_time_patterns`

Analyze viewing patterns by time of day and day of week.

**Returns:**
```json
{
  "peak_hours": [23, 0, 22],
  "peak_days": ["Saturday", "Sunday"],
  "late_night_ratio": 0.35,
  "weekend_ratio": 0.45,
  "hourly_distribution": {"0": 45, "1": 38, ...},
  "insight": "You're a night owl - 35% of videos watched between midnight and 5am"
}
```

---

### `generate_music_prompt`

Generate a single Suno AI music prompt based on taste profile.

**Returns:**
```json
{
  "taste_profile": {
    "primary_genres": ["Lo-fi", "Jazz", "Indie"],
    "mood_keywords": ["chill", "dreamy", "melancholic"],
    "energy_level": "low",
    "time_context": "late_night",
    "language_preference": "mixed"
  },
  "suno_prompt": {
    "style": "Lo-fi, Jazz, Indie",
    "mood": "chill, dreamy, melancholic",
    "tempo": "60-85 BPM",
    "instruments": "vinyl crackle, mellow piano, soft drums",
    "full_prompt": "Lo-fi, Jazz, Indie, chill, dreamy, 60-85 BPM, vinyl crackle, mellow piano"
  }
}
```

---

## Advanced Analysis Tools

### `get_channel_stats`

Get detailed statistics for a specific channel.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_name` | string | Yes | Channel name (partial match) |

**Returns:**
```json
{
  "channel": "Lofi Girl",
  "total_videos": 156,
  "first_watched": "2024-01-15T23:30:00",
  "last_watched": "2024-12-20T02:15:00",
  "viewing_period_days": 340,
  "peak_hours": [23, 0, 1],
  "peak_days": ["Friday", "Saturday"]
}
```

---

### `get_monthly_trends`

Analyze monthly viewing patterns and growth trends.

**Returns:**
```json
{
  "months": [
    {
      "month": "2024-01",
      "video_count": 89,
      "top_categories": ["music", "gaming"],
      "top_channels": ["Lofi Girl", "GameChannel"],
      "avg_daily": 2.9
    }
  ],
  "total_months": 12,
  "trend": "increasing",
  "growth_percent": 23.5
}
```

---

### `get_content_by_time`

Analyze content types watched at different times of day.

**Returns:**
```json
{
  "time_slots": [
    {
      "slot": "late_night",
      "hours": "00:00-05:00",
      "video_count": 234,
      "top_categories": ["music"],
      "top_keywords": ["lofi", "chill", "sleep"]
    },
    {
      "slot": "morning",
      "hours": "05:00-12:00",
      "video_count": 89,
      "top_categories": ["education", "tech"]
    }
  ],
  "insights": [
    "Late Night: primarily music content",
    "Morning: primarily education content"
  ]
}
```

---

### `detect_phases`

Detect distinct viewing phases based on content pattern changes.

**Returns:**
```json
{
  "phases": [
    {
      "period": "2024.06 - 2024.08",
      "name": "Gaming Focus",
      "categories": ["gaming"],
      "video_count": 456,
      "description": "10 weeks of gaming focus (456 videos)"
    },
    {
      "period": "2024.09 - 2024.11",
      "name": "Music Exploration",
      "categories": ["music"],
      "video_count": 234
    }
  ],
  "total_phases": 2
}
```

---

### `get_diversity_score`

Calculate channel diversity using Shannon entropy.

**Returns:**
```json
{
  "overall_score": 72.5,
  "channel_entropy": 4.23,
  "top_channel_concentration": 35.2,
  "unique_ratio": 0.15,
  "interpretation": "Highly diverse - you explore many different channels"
}
```

**Score Interpretation:**
- 70-100: Highly diverse
- 50-69: Moderately diverse
- 30-49: Focused viewer
- 0-29: Very focused

---

## Generation & Export Tools

### `generate_music_prompts`

Generate multiple Suno prompt variations.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `count` | integer | No | 3 | Number of prompts (1-5) |

**Returns:**
```json
{
  "prompts": [
    {
      "label": "Main Style",
      "style": "Lo-fi, Jazz",
      "mood": "chill, dreamy",
      "tempo": "60-85 BPM",
      "instruments": "vinyl crackle, piano",
      "full_prompt": "..."
    },
    {
      "label": "Energy Variation",
      "mood": "uplifting, energetic",
      "tempo": "90-110 BPM"
    },
    {
      "label": "Mood Variation",
      "mood": "upbeat, happy"
    }
  ],
  "count": 3
}
```

**Variation Types:**
1. **Main Style**: Based directly on analysis
2. **Energy Variation**: Higher/lower energy version
3. **Mood Variation**: Contrasting mood
4. **Instrument Variation**: Alternative instruments
5. **Genre Fusion**: Hybrid genre style

---

### `suggest_content`

Get content recommendations based on taste profile.

**Returns:**
```json
{
  "current_favorites": ["Lofi Girl", "Jazz Cafe", "Indie Vibes"],
  "primary_genres": ["Lo-fi", "Jazz", "Indie"],
  "suggestions": {
    "based_on_genres": ["Study playlists", "Smooth jazz collections"],
    "explore_new": ["Podcasts about music", "Film analysis"],
    "time_based": {
      "late_night": ["Relaxing content", "ASMR", "Ambient music"]
    }
  }
}
```

---

### `export_analysis`

Export complete analysis in markdown or JSON format.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `format` | string | No | "markdown" | "markdown" or "json" |

**Returns (markdown):**
```json
{
  "format": "markdown",
  "content": "# YouTube Watch History Analysis Report\n\n## Overview\n..."
}
```

**Returns (json):**
```json
{
  "format": "json",
  "content": {
    "statistics": {...},
    "topics": {...},
    "time_patterns": {...},
    "diversity": {...}
  }
}
```

---

## Caching Tools

### `load_cached_data`

Restore previously analyzed data after server restart.

**Returns:**
```json
{
  "status": "loaded",
  "file_path": "/path/to/watch-history.json",
  "total_videos": 1234,
  "unique_channels": 89,
  "message": "Loaded 1234 videos from cache"
}
```

---

### `clear_cache`

Clear cached watch history data.

**Returns:**
```json
{
  "status": "cleared",
  "message": "Cache cleared successfully"
}
```

**Cache Location:** `~/.mirror_mcp_cache.json`
