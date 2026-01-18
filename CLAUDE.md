# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install with all dependencies
pip install -e ".[all,dev]"

# Install specific apps only
pip install -e ".[duplikate]"   # DupliKate
pip install -e ".[reddit]"      # RedditBrowser
pip install -e ".[video]"       # Video downloading (TransCoda)

# Run all tests
pytest

# Run tests for a specific module
pytest Imageplay/tests/
pytest FileWrangler/test__Separator/
pytest TransCoda/tests/

# Linting
ruff check .

# Type checking
mypy <module>
```

## Running Applications

After installation, run via entry points:
```bash
imageplay
transcoda
filewrangler
duplikate
```

## Repository Architecture

This is a monorepo containing multiple PyQt5 desktop applications that share common utilities.

### Applications

| App | Purpose | Entry Point |
|-----|---------|-------------|
| **Imageplay** | Image slideshow with editing | `Imageplay.ImagePlayApp:main` |
| **TransCoda** | FFmpeg-based media transcoder | `TransCoda.TransCodaApp:main` |
| **FileWrangler** | Pattern-based file manipulation | `FileWrangler.FileWranglerApp:main` |
| **DupliKate** | Duplicate image finder | `DupliKate.ImageDuplicateFinderDialog:main` |
| **RoboGui** | Robocopy GUI wrapper | `RoboGui/src/RoboGui.py` |

### Common Package (`common/`)

All applications depend on shared utilities in `common/`:

- **CommonUtils.py**: Logging (`get_logger`), file hashing, human-readable sizes/times, cross-platform file opening, `PausableTimer`, `FileScanner`
- **CustomUI.py**: Reusable widgets - `FileChooserTextBox`, `DropZone`
- **MediaMetaData.py**: FFprobe/ImageMagick metadata extraction
- **Theme.py**: Icon caching and theme management

### Application Structure Pattern

Each application follows this structure:
```
AppName/
├── AppNameApp.py      # Main window, QApplication entry
├── core/              # Business logic
├── ui/                # PyQt5 widgets and dialogs
├── tests/             # Pytest tests
└── __init__.py        # App metadata, logger
```

### Key Architectural Patterns

- **Event-driven**: PyQt signals for component communication (e.g., `files_dropped_event`, `button_pressed`)
- **Settings persistence**: QSettings via per-app settings modules
- **Cross-platform**: `sys.platform` checks for OS-specific behavior

## System Requirements

External tools required by some features:
- `ffprobe` (FFmpeg) - Media metadata extraction
- `magick` (ImageMagick) - Image identification

## Test Configuration

Test patterns recognized by pytest (from `pyproject.toml`):
- Files: `test_*.py`, `Test*.py`, `UT*.py`
- Classes: `Test*`, `UT*`
- Functions: `test_*`
