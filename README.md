# BlueWriter

A modern fiction writing application built with Python and Qt (PySide6), featuring AI assistant integration through the Model Context Protocol (MCP).

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-197%20passing-brightgreen.svg)

## Features

- 📚 **Project Organization** - Manage multiple writing projects with stories and chapters
- 🗒️ **Visual Canvas** - Arrange chapters as sticky notes on an infinite canvas
- 📝 **Rich Text Editor** - Full-featured editor with formatting toolbar
- 📖 **Encyclopedia** - World-building database for characters, locations, items, and more
- 🤖 **AI Integration** - Control BlueWriter through Claude and other AI assistants via MCP
- 💾 **Auto-Save** - Never lose your work with automatic saving

## Screenshots

*Coming soon*

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/AltonLord/BlueWriter.git
cd BlueWriter
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run BlueWriter:
```bash
python main.py
```

## Usage

### Basic Workflow

1. **Create a Project** - Start by creating a new project for your novel or story collection
2. **Add Stories** - Create one or more stories within your project
3. **Write Chapters** - Add chapters as sticky notes on the canvas, then double-click to edit
4. **Build Your World** - Use the Encyclopedia to track characters, locations, and lore
5. **Publish** - Mark stories as complete when finished

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New Chapter | `Ctrl+N` |
| Save | `Ctrl+S` |
| Find/Replace | `Ctrl+F` |
| Bold | `Ctrl+B` |
| Italic | `Ctrl+I` |
| Underline | `Ctrl+U` |

## AI Integration (MCP)

BlueWriter can be controlled by AI assistants like Claude through the Model Context Protocol.

### Setup for Claude Desktop

1. Ensure BlueWriter is installed and working
2. Add to your Claude Desktop config (`~/.config/claude-desktop/config.json`):

```json
{
  "mcpServers": {
    "bluewriter": {
      "command": "python",
      "args": ["-m", "bluewriter_mcp.bluewriter_server"],
      "cwd": "/path/to/BlueWriter",
      "env": {
        "PYTHONPATH": "/path/to/BlueWriter"
      }
    }
  }
}
```

3. Restart Claude Desktop
4. Launch BlueWriter (the app must be running for MCP to work)
5. Ask Claude to interact with your projects!

### Example Prompts

- "List my BlueWriter projects"
- "Create a new chapter called 'The Discovery' in story 1"
- "Show me all characters in my encyclopedia"
- "Move chapter 3 to position 500, 200 on the canvas"
- "Write an opening paragraph for chapter 1"

### Available Tools

BlueWriter provides **46 MCP tools** in 6 categories:

| Category | Tools | Examples |
|----------|-------|----------|
| Project | 6 | list, create, open, delete |
| Story | 9 | create, publish, reorder |
| Chapter | 13 | create, move, edit content |
| Encyclopedia | 9 | create, search, categorize |
| Canvas | 6 | pan, zoom, focus, fit |
| State | 3 | get state, save all |

See [docs/MCP_TOOLS.md](docs/MCP_TOOLS.md) for complete documentation.

## REST API

BlueWriter exposes a REST API on `http://127.0.0.1:5000` when running.

### Quick Reference

```bash
# List projects
curl http://127.0.0.1:5000/projects

# Create a project
curl -X POST http://127.0.0.1:5000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Novel"}'

# Get chapter content
curl http://127.0.0.1:5000/chapters/1
```

### Documentation

- **Swagger UI**: http://127.0.0.1:5000/docs
- **ReDoc**: http://127.0.0.1:5000/redoc
- **Full API Docs**: [docs/API.md](docs/API.md)

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov=api --cov=events

# Run specific test category
pytest tests/test_services/ -v
pytest tests/test_api/ -v
pytest tests/test_mcp/ -v
```

### Project Structure

```
BlueWriter/
├── main.py                 # Application entry point
├── views/                  # Qt UI components
├── models/                 # Data models
├── services/               # Business logic layer
├── api/                    # REST API (FastAPI)
├── events/                 # Event bus system
├── adapters/               # Qt adapter for events
├── bluewriter_mcp/         # MCP server
├── database/               # SQLite database layer
├── tests/                  # Test suite (197 tests)
├── docs/                   # Documentation
└── data/                   # User data (database, dictionaries)
```

### Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  MCP Server     │────▶│   REST API      │
│  (Claude, etc.) │     │   (FastAPI)     │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  Service Layer  │
                        │  (Business Logic)│
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
     │   Event Bus     │ │  Database   │ │   Qt Adapter    │
     │  (Pub/Sub)      │ │  (SQLite)   │ │  (UI Updates)   │
     └─────────────────┘ └─────────────┘ └────────┬────────┘
                                                  │
                                         ┌────────▼────────┐
                                         │    Qt UI        │
                                         │  (PySide6)      │
                                         └─────────────────┘
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) (Qt for Python)
- REST API powered by [FastAPI](https://fastapi.tiangolo.com/)
- MCP integration using [mcp](https://modelcontextprotocol.io/)

## Support

If you encounter any issues or have questions:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/AltonLord/BlueWriter/issues)
3. Open a new issue if needed

---

Made with ❤️ for writers who want AI assistance in their creative process.
