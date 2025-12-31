# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Desktop                          │
│                                                               │
│   User: "Analyze my YouTube history"                         │
│              │                                                │
│              ▼                                                │
│   ┌─────────────────────┐                                    │
│   │   MCP Client        │                                    │
│   └─────────────────────┘                                    │
│              │                                                │
└──────────────│────────────────────────────────────────────────┘
               │ MCP Protocol (stdio)
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mirror MCP Server                         │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    server.py                          │   │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │   │
│   │  │  14 MCP   │ │   State   │ │  Cache Manager    │  │   │
│   │  │   Tools   │ │  Manager  │ │ (~/.mirror_cache) │  │   │
│   │  └───────────┘ └───────────┘ └───────────────────┘  │   │
│   └─────────────────────────────────────────────────────┘   │
│              │                                                │
│              ▼                                                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    Analyzers                          │   │
│   │  ┌────────────┐ ┌────────────┐ ┌────────────────┐   │   │
│   │  │ statistics │ │   topics   │ │ time_patterns  │   │   │
│   │  │            │ │            │ │                │   │   │
│   │  │ - stats    │ │ - keywords │ │ - patterns     │   │   │
│   │  │ - diversity│ │ - synonyms │ │ - trends       │   │   │
│   │  │            │ │ - category │ │ - phases       │   │   │
│   │  └────────────┘ └────────────┘ └────────────────┘   │   │
│   └─────────────────────────────────────────────────────┘   │
│              │                                                │
│              ▼                                                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   Generators                          │   │
│   │  ┌──────────────────────────────────────────────┐   │   │
│   │  │              suno_prompt.py                    │   │   │
│   │  │                                                │   │   │
│   │  │  TasteProfile → SunoPrompt (≤200 chars)       │   │   │
│   │  │  + Energy/Mood/Instrument/Fusion variations   │   │   │
│   │  └──────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────┘   │
│              │                                                │
│              ▼                                                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                     Parsers                           │   │
│   │  ┌──────────────────────────────────────────────┐   │   │
│   │  │               youtube.py                       │   │   │
│   │  │                                                │   │   │
│   │  │  Google Takeout JSON → WatchHistoryEntry[]    │   │   │
│   │  └──────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────┘   │
│              │                                                │
└──────────────│────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Google Takeout                          │   │
│   │                                                       │   │
│   │   watch-history.json                                 │   │
│   │   [{"title": "Watched ...", "time": "..."}]         │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Module Structure

```
src/mirror_mcp/
├── __init__.py
├── server.py              # MCP server entry point
├── models.py              # Pydantic data models
├── parsers/
│   ├── __init__.py
│   └── youtube.py         # Google Takeout parser
├── analyzers/
│   ├── __init__.py
│   ├── statistics.py      # Basic stats & diversity
│   ├── topics.py          # Keywords & categories
│   └── time_patterns.py   # Time analysis & phases
├── generators/
│   ├── __init__.py
│   └── suno_prompt.py     # Prompt generation
└── utils/
    └── __init__.py
```

## Data Flow

### 1. Parsing Phase

```
watch-history.json
        │
        ▼
┌───────────────────┐
│  parse_watch_     │
│  history()        │
└───────────────────┘
        │
        ▼
List[WatchHistoryEntry]
  - title: str
  - titleUrl: str
  - time: datetime
  - subtitles: [ChannelInfo]
```

### 2. Analysis Phase

```
List[WatchHistoryEntry]
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  statistics  │  │    topics    │  │time_patterns │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
WatchStatistics    TopicAnalysis      TimePattern
DiversityScore     (normalized)       MonthlyTrend[]
                                      WatchingPhase[]
```

### 3. Generation Phase

```
TopicAnalysis + TimePattern
        │
        ▼
┌───────────────────┐
│ build_taste_      │
│ profile()         │
└───────────────────┘
        │
        ▼
   TasteProfile
  - primary_genres
  - mood_keywords
  - energy_level
  - tempo_preference
        │
        ▼
┌───────────────────┐
│ generate_suno_    │
│ prompt()          │
└───────────────────┘
        │
        ▼
   SunoPrompt
  - full_prompt (≤200 chars)
```

## Data Models

### Core Models

```python
class WatchHistoryEntry(BaseModel):
    """Single video from Google Takeout"""
    title: str
    titleUrl: Optional[str]
    time: datetime
    subtitles: list[ChannelInfo]

    @property
    def clean_title(self) -> str:
        """Remove 'Watched ' prefix"""

    @property
    def channel_name(self) -> Optional[str]:
        """Get channel name from subtitles"""
```

### Analysis Models

```python
class TopicAnalysis(BaseModel):
    keywords: list[tuple[str, int]]      # [("lofi", 89), ...]
    language_breakdown: dict[str, int]   # {"korean": 234, "english": 456}
    categories: list[str]                # ["music", "gaming"]

class TimePattern(BaseModel):
    peak_hours: list[int]                # [23, 0, 22]
    peak_days: list[str]                 # ["Saturday", "Sunday"]
    late_night_ratio: float              # 0.35
    weekend_ratio: float                 # 0.45

class DiversityScore(BaseModel):
    overall_score: float                 # 0-100
    channel_entropy: float               # Shannon entropy
    top_channel_concentration: float     # % from top 5
    interpretation: str                  # Human-readable
```

### Generation Models

```python
class TasteProfile(BaseModel):
    primary_genres: list[str]            # ["Lo-fi", "Jazz"]
    mood_keywords: list[str]             # ["chill", "dreamy"]
    energy_level: str                    # "low" | "medium" | "high"
    tempo_preference: str                # "slow" | "moderate" | "fast"
    time_context: str                    # "late_night" | "morning" | ...
    language_preference: str             # "korean" | "english" | "mixed"

class SunoPrompt(BaseModel):
    style_tags: str                      # "Lo-fi, Jazz, Indie"
    mood: str                            # "chill, dreamy"
    tempo_bpm: str                       # "60-85 BPM"
    instruments: str                     # "vinyl crackle, piano"
    full_prompt: str                     # ≤200 chars combined
```

## Key Algorithms

### Synonym Normalization

```python
SYNONYMS = {
    "kpop": ["k-pop", "케이팝", "k pop"],
    "lofi": ["lo-fi", "로파이", "lo fi"],
    "hiphop": ["hip-hop", "힙합", "hip hop"],
}

def normalize_keyword(word: str) -> str:
    return _SYNONYM_LOOKUP.get(word.lower(), word.lower())
```

### Diversity Score (Shannon Entropy)

```python
def calculate_diversity_score(entries):
    # Count videos per channel
    channel_counts = Counter(e.channel_name for e in entries)

    # Calculate Shannon entropy
    entropy = 0.0
    total = sum(channel_counts.values())
    for count in channel_counts.values():
        p = count / total
        entropy -= p * math.log2(p)

    # Normalize to 0-100 scale
    max_entropy = math.log2(total)
    normalized = (entropy / max_entropy) * 100

    return normalized
```

### Phase Detection

```python
def detect_phases(entries):
    # Group by week
    weekly_data = group_by_week(entries)

    # Find dominant category per week
    weekly_categories = [
        (week, get_dominant_category(week_entries))
        for week, week_entries in weekly_data
    ]

    # Detect category changes
    phases = []
    current_category = None
    for week, category in weekly_categories:
        if category != current_category:
            # New phase started
            phases.append(Phase(...))
            current_category = category

    return phases
```

## Caching Strategy

### Cache File Structure

```json
{
  "file_path": "/path/to/watch-history.json",
  "entries": [
    {
      "title": "Watched Lo-fi beats",
      "titleUrl": "https://...",
      "time": "2024-12-15T02:30:00",
      "subtitles": [{"name": "Lofi Girl", "url": "..."}]
    }
  ]
}
```

### Cache Operations

```python
# Auto-save on analyze
def analyze_watch_history(file_path):
    entries = parse_watch_history(file_path)
    _state["entries"] = entries
    _save_cache()  # Persist to ~/.mirror_mcp_cache.json
    return analyze(entries)

# Manual load
def load_cached_data():
    if _load_cache():
        return {"status": "loaded", ...}
    return {"status": "no_cache"}

# Manual clear
def clear_cache():
    CACHE_FILE.unlink()
    _state["entries"] = None
```

## Extension Points

### Adding New Parsers

```python
# src/mirror_mcp/parsers/netflix.py
from ..models import WatchHistoryEntry

def parse_netflix_history(file_path: str) -> list[WatchHistoryEntry]:
    """Parse Netflix viewing activity CSV"""
    # Convert Netflix format to unified WatchHistoryEntry
    pass
```

### Adding New Analyzers

```python
# src/mirror_mcp/analyzers/sentiment.py
def analyze_sentiment(entries: list[WatchHistoryEntry]) -> SentimentAnalysis:
    """Analyze emotional sentiment from video titles"""
    pass
```

### Adding New MCP Tools

```python
# In server.py
@mcp.tool()
def new_tool(param: str) -> dict:
    """New analysis tool"""
    if _state["entries"] is None:
        return {"error": "Please call analyze_watch_history first"}

    # Perform analysis
    result = do_analysis(_state["entries"])
    return {"result": result}
```
