# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FileFolderRenamer is a Python desktop application designed for file and folder renaming operations. The project is in early development stages (v0.0.0) and uses PyInstaller for building standalone executables.

## Project Structure

```
FileFolderRenamer/
├── app/           # Main application code
├── service/       # Business logic and service layer
├── utils/         # Utility modules (config management, helpers)
├── scripts/       # Build and maintenance scripts
├── tests/         # Test suite
└── docs/          # Documentation
```

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest tests/ -v --tb=short

# Run tests with coverage
python -m pytest tests/ -v --tb=short --coverage

# Run without warnings
python -m pytest tests/ -v --tb=short --disable-warnings
```

### Type Checking
```bash
# Run pyright type checker
pyright
```

The project uses pyright with standard type checking mode. Type checking covers `app/`, `service/`, and `utils/` directories, excluding `tests/` and `scripts/`.

### Building
```bash
# Build executable
python build.py
```

The build process:
1. Automatically increments the patch version in `app/__init__.py`
2. Updates version metadata in `docs/README.md`
3. Builds a windowed executable using PyInstaller
4. Bundles `utils/config.ini` with the executable

## Architecture

### Configuration Management (`utils/config_manager.py`)

The application uses a dual configuration system:
- **INI files** (`utils/config.ini`) for application settings

### Version Management (`scripts/version_manager.py`)

Version tracking is maintained in two locations:
- `app/__init__.py`: `__version__` and `__date__` constants
- `docs/README.md`: User-facing version and date information

The version manager automatically:
- Reads current version from `app/__init__.py`
- Increments patch version
- Updates both files with new version and current date
- Returns the new version string

### Project Structure Generation (`scripts/project_structure.py`)

Utility for generating ASCII tree representations of the project. Ignores common build artifacts, virtual environments, and IDE files. Can be used to document project structure or for debugging.

## Configuration Files

### `pyrightconfig.json`
Type checking configuration:
- Python version: 3.13
- Type checking mode: standard
- Includes: app, service, utils
- Excludes: tests, scripts
- Reports unused variables and imports

### `utils/config.ini`
Application configuration (not version controlled):
- Contains path configurations and user-specific settings
- **Note**: This file is modified by users and may contain local paths

## Development Notes

### PyInstaller Compatibility
The config manager handles both development and packaged environments:
- In development: Reads config from `utils/config.ini`
- When frozen (PyInstaller): Reads from `sys._MEIPASS` directory

### Testing
Test files are currently minimal (empty test_main.py). When adding tests:
- Place in `tests/` directory
- Use pytest framework
- Tests are excluded from pyright type checking
