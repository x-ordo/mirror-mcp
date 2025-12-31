# Installation Guide

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/x-ordo/mirror-mcp.git
cd mirror-mcp
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Optional: Korean NLP Support

For better Korean keyword extraction:

```bash
uv sync --extra korean
```

This installs [KoNLPy](https://konlpy.org/) for advanced Korean natural language processing.

## Claude Desktop Integration

### Configuration

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mirror": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/mirror-mcp", "run", "mirror-mcp"]
    }
  }
}
```

### Verify Installation

1. Restart Claude Desktop
2. Open a new conversation
3. You should see "mirror" in the available MCP servers
4. Try: "Analyze my YouTube history from /path/to/watch-history.json"

## Getting Your Watch History

### From Google Takeout

1. Go to [Google Takeout](https://takeout.google.com/)
2. Click "Deselect all"
3. Scroll down and select "YouTube and YouTube Music"
4. Click "All YouTube data included" and select only "history"
5. Click "Next step"
6. Choose "Export once" and ".zip" format
7. Click "Create export"
8. Download and extract the ZIP file
9. Find `watch-history.json` in the extracted folder

### File Location

The file is typically at:
```
Takeout/YouTube and YouTube Music/history/watch-history.json
```

## Development Setup

### Install Dev Dependencies

```bash
uv sync --extra dev
```

### Run Tests

```bash
uv run pytest -v
```

### Run Server Directly

```bash
uv run mirror-mcp
```

## Troubleshooting

### "Command not found: uv"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### KoNLPy Installation Issues

On macOS, you may need Java:
```bash
brew install openjdk
```

On Ubuntu/Debian:
```bash
sudo apt-get install default-jdk
```

### MCP Server Not Appearing in Claude

1. Check the config file path is correct
2. Ensure the path to mirror-mcp is absolute
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors
