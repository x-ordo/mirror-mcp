# Mirror MCP

MCP server for YouTube watch history analysis and Suno prompt generation.

## Features

- Parse Google Takeout `watch-history.json`
- Extract keywords from video titles (Korean + English)
- Analyze viewing patterns (time of day, day of week)
- Generate Suno AI music prompts based on taste profile

## Installation

```bash
# Using uv (recommended)
uv sync

# With optional Korean NLP support
uv sync --extra korean
```

## Usage with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

Then in Claude Desktop:

```
1. "Analyze my YouTube history from /path/to/watch-history.json"
2. "What are my top topics?"
3. "When do I usually watch videos?"
4. "Generate a music prompt based on my taste"
```

## MCP Tools

### Core Analysis
| Tool | Description |
|------|-------------|
| `analyze_watch_history(file_path)` | Parse Google Takeout JSON and extract statistics |
| `get_top_topics(limit=20)` | Extract top keywords from video titles (with synonym normalization) |
| `get_time_patterns()` | Analyze viewing patterns by time and day |
| `generate_music_prompt()` | Generate Suno-compatible music prompt |

### Advanced Analysis
| Tool | Description |
|------|-------------|
| `get_channel_stats(channel_name)` | Detailed statistics for a specific channel |
| `get_monthly_trends()` | Monthly viewing patterns and trend analysis |
| `get_content_by_time()` | Content types watched at different times of day |
| `detect_phases()` | Detect distinct viewing phases (e.g., "Gaming Focus", "Music Exploration") |
| `get_diversity_score()` | Channel diversity metrics (entropy-based) |

### Generation & Export
| Tool | Description |
|------|-------------|
| `generate_music_prompts(count=3)` | Generate multiple varied Suno prompts |
| `suggest_content()` | Content recommendations based on taste profile |
| `export_analysis(format="markdown")` | Export complete analysis (markdown or JSON) |

### Caching
| Tool | Description |
|------|-------------|
| `load_cached_data()` | Restore data after server restart |
| `clear_cache()` | Clear cached watch history |

## Getting Your Watch History

1. Go to [Google Takeout](https://takeout.google.com/)
2. Deselect all, then select only "YouTube and YouTube Music"
3. Under "YouTube", select only "history"
4. Choose JSON format
5. Download and extract the `watch-history.json` file

## Example Output

```json
{
  "suno_prompt": {
    "style": "Lo-fi, Jazz, Indie",
    "mood": "chill, Melancholic, Dreamy",
    "tempo": "60-85 BPM",
    "instruments": "vinyl crackle, mellow piano, soft drums",
    "full_prompt": "Lo-fi, Jazz, Indie, chill, Melancholic, Dreamy, 60-85 BPM, vinyl crackle, mellow piano, soft drums"
  }
}
```

## Development

```bash
# Run tests
uv run pytest

# Run server directly
uv run mirror-mcp
```

## License

MIT
