# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project Mirror** is an MCP (Model Context Protocol) server that analyzes users' YouTube watch history from Google Takeout to discover deep interests and generate optimized prompts for AI music creation tools like Suno.

Core concept: "The algorithm knows me better than I know myself."

## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run mirror-mcp

# Run with Python directly
python -m mirror_mcp.server

# Install with optional Korean NLP support
uv sync --extra korean

# Run tests
uv run pytest
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mirror": {
      "command": "uv",
      "args": ["--directory", "/path/to/mirror-mcp", "run", "mirror-mcp"]
    }
  }
}
```

## Architecture

```
src/mirror_mcp/
├── server.py           # MCP server with FastMCP (14 tools, caching)
├── models.py           # Pydantic data models (10 models)
├── parsers/
│   └── youtube.py      # Google Takeout JSON parser
├── analyzers/
│   ├── statistics.py   # Watch statistics, diversity score
│   ├── topics.py       # Keyword extraction with synonym normalization
│   └── time_patterns.py # Time patterns, monthly trends, phase detection
└── generators/
    └── suno_prompt.py  # Taste profile → Suno prompt (with variations)
```

## MCP Tools (14 Total)

### Core Analysis
| Tool | Description |
|------|-------------|
| `analyze_watch_history(file_path)` | Parse Google Takeout JSON, return statistics |
| `get_top_topics(limit)` | Extract keywords with synonym normalization |
| `get_time_patterns()` | Analyze viewing patterns by time/day |
| `generate_music_prompt()` | Generate Suno-compatible music prompt |

### Advanced Analysis
| Tool | Description |
|------|-------------|
| `get_channel_stats(channel_name)` | Detailed statistics for specific channel |
| `get_monthly_trends()` | Monthly viewing patterns and growth analysis |
| `get_content_by_time()` | Content types by time slot (late night, morning, etc.) |
| `detect_phases()` | Detect viewing phases (e.g., "Gaming Focus") |
| `get_diversity_score()` | Shannon entropy-based channel diversity |

### Generation & Export
| Tool | Description |
|------|-------------|
| `generate_music_prompts(count)` | Multiple Suno prompt variations |
| `suggest_content()` | Content recommendations based on taste |
| `export_analysis(format)` | Export as markdown or JSON |

### Caching
| Tool | Description |
|------|-------------|
| `load_cached_data()` | Restore data after server restart |
| `clear_cache()` | Clear cached watch history |

## Data Models

```python
# Core models
WatchHistoryEntry    # Single video entry from Takeout
WatchStatistics      # Overall stats (total, channels, date range)
TopicAnalysis        # Keywords, language breakdown, categories
TimePattern          # Peak hours, days, late night/weekend ratios

# Advanced models
MonthlyTrend         # Per-month video count and categories
ContentTimeCorrelation # Content types by time slot
WatchingPhase        # Detected viewing phases
DiversityScore       # Entropy-based diversity metrics

# Generation models
TasteProfile         # Genres, moods, energy, tempo
SunoPrompt           # Style, mood, tempo, instruments
```

## Data Flow

1. User provides Google Takeout `watch-history.json` path
2. `analyze_watch_history()` parses, stores in memory, and saves to cache
3. Other tools analyze the stored data (topics, patterns, diversity, phases)
4. `generate_music_prompt()` or `generate_music_prompts()` creates Suno prompts
5. `export_analysis()` outputs comprehensive report

## Key Implementation Notes

### State Management
- In-memory state (`_state`) stores parsed entries between tool calls
- Cache file (`~/.mirror_mcp_cache.json`) persists data across restarts
- `load_cached_data()` restores state without re-parsing

### Keyword Processing
- Synonym normalization: "k-pop", "케이팝", "kpop" → "kpop"
- Bilingual support: Korean (regex + optional KoNLPy) + English
- Category inference from keywords

### Time Analysis
- Late-night detection (00:00-05:00) for mood inference
- Monthly trend analysis with growth calculation
- Phase detection based on category shifts

### Prompt Generation
- Single prompt: `generate_music_prompt()`
- Multiple variations: `generate_music_prompts(count)` with:
  - Energy variation (tempo shift)
  - Mood variation (contrasting moods)
  - Instrument variation (alternative instruments)
  - Genre fusion variation (hybrid styles)
- All prompts respect Suno's 200 character limit

### Diversity Metrics
- Shannon entropy for channel distribution
- Top-5 channel concentration percentage
- Unique channel ratio
- Interpreted as: Highly diverse / Moderately diverse / Focused / Very focused
