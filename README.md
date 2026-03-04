# Archai - AI Architecture CLI Tool

An interactive CLI tool that uses multiple AI backends to generate and transform software architectures.

---

## Table of Contents

1. [Features](#features)
2. [Supported Architectures](#supported-architectures)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [Experiments & Research](#experiments--research)
8. [Project Structure](#project-structure)
9. [Development](#development)

---

## Features


- **Multiple AI Providers**: Claude CLI, OpenAI, LiteLLM
- **5 Architecture Patterns**: Monolithic, Microservices, Serverless, Event-Driven, Hexagonal
- **Architecture Transformation**: Convert existing codebases between architectures
- **Code Generation**: AI generates complete, runnable code with structure

---

## Supported Architectures

| Architecture | Description | Output |
|--------------|-------------|--------|
| **Monolithic** | Single deployable unit with layered structure (Controller/Service/Repository) | Single file or directory |
| **Microservices** | Independent services with API gateway, Docker orchestration | Multiple services + docker-compose |
| **Serverless** | AWS Lambda-style functions with event triggers | Functions + serverless.yml |
| **Event-Driven** | Message bus, pub/sub pattern, async processing | Event handlers + message bus |
| **Hexagonal** | Ports & adapters, clean architecture, dependency inversion | Domain/Ports/Adapters structure |

---

## Installation

### Linux / macOS

```bash
# Clone the repository
git clone <repo-url>
cd archai

# Install from source
pip install -e .

# Or with pipx (recommended for CLI tools)
pipx install .
```

### Windows

#### How to run

```powershell
# 1. Install Python 3.10+ from python.org or Microsoft Store
# Make sure to check "Add Python to PATH" during installation

# 2. Download/extract or clone the repository
# If downloaded as ZIP, extract it first

# 3. Navigate to PROJECT ROOT (where pyproject.toml is located)
cd C:\Users\YourName\Downloads\archai-main\archai-main
# Or if cloned:
cd archai

# IMPORTANT: You must be in the folder containing pyproject.toml, NOT inside archai subfolder!
# Verify with: dir pyproject.toml (should show the file)

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run with Python module syntax (from project root!)
python -m archai -p claude-cli
```

> **Common Error:** `ModuleNotFoundError: No module named 'archai'`
> This means you're in the wrong directory. Make sure you're in the project root (where `pyproject.toml` is), not inside the `archai/` subfolder.

### Prerequisites

#### For Claude CLI provider (recommended):

**Linux/macOS:**
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Login to Claude
claude login
```

**Windows (PowerShell):**
```powershell
# 1. Install Node.js from https://nodejs.org/ (LTS version)

# 2. Install Claude CLI
npm install -g @anthropic-ai/claude-code

# 3. Login to Claude
claude login
```

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Login
claude login
```

#### For Ollama provider (local models):

**Windows:**
1. Download Ollama from https://ollama.ai/download/windows
2. Run installer
3. Open PowerShell and run:
```powershell
ollama pull llama3.2
archai -p ollama -m llama3.2
```

**Linux/macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2
```

## Quick Start

**Linux/macOS:**
```bash
# Start with Claude CLI (uses your Claude subscription)
archai -p claude-cli

# Use specific model
archai -p claude-cli -m opus    # Most capable
archai -p claude-cli -m haiku   # Fastest

# Use OpenAI
archai -p openai -k $OPENAI_API_KEY

**Windows (PowerShell):**
```powershell
# Start with Claude CLI
archai -p claude-cli

# Use specific model
archai -p claude-cli -m opus    # Most capable
archai -p claude-cli -m haiku   # Fastest

# Use OpenAI (set environment variable first)
$env:OPENAI_API_KEY = "sk-your-key-here"
archai -p openai -k $env:OPENAI_API_KEY

# Use local Ollama
archai -p ollama -m llama3.2
```

### Generation Commands

| Command Pattern | Description | Example |
|-----------------|-------------|---------|
| `create a monolithic [app] at [path]` | Generate monolithic app | `create a monolithic todo app at ./todo` |
| `create a microservices [app] at [path]` | Generate microservices | `create a microservices api at ./api` |
| `create a serverless [app] at [path]` | Generate Lambda functions | `create a serverless calculator at ./calc` |
| `create an event-driven [app] at [path]` | Generate event-based app | `create an event-driven processor at ./proc` |
| `create a hexagonal [app] at [path]` | Generate clean architecture | `create a hexagonal shop at ./shop` |

### Transformation Commands

| Command Pattern | Description |
|-----------------|-------------|
| `rewrite [source] to microservices at [target]` | Convert monolithic to microservices |
| `rewrite [source] to [architecture] at [target]` | Convert to any architecture |

### Built-in Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/config` | View or modify configuration |
| `/clear` | Clear the screen |
| `/providers` | List available AI providers |
| `/architectures` | List supported architectures |
| `/exit` or `exit` | Exit the application |

---

## Configuration

Configuration file: `~/.archai/config.yaml`

```yaml
default_provider: claude-cli

providers:
  claude-cli:                      # Uses Claude subscription (no API key!)
    model: opus                    # opus, sonnet, haiku
    timeout: 300

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514

  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o

  ollama:
    base_url: http://localhost:11434
    model: llama3.2

  litellm:
    base_url: http://localhost:8000/v1  # Custom endpoint
    model: openai/my-model

default_language: python
theme: dark
```

### Environment Variables

```bash
# For OpenAI provider
export OPENAI_API_KEY=sk-...

# For Anthropic API provider
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Experiments & Research

The `experiments/` folder contains comprehensive research comparing AI models on architecture generation tasks.

### Experiment Structure

```
experiments/
├── calculator/
│   ├── monolithic/
│   │   ├── claude-opus/main.py       # 362 lines
│   │   ├── claude-haiku/main.py      # 207 lines
│   │   ├── openai-gpt4/main.py       # 71 lines
│   │   ├── claude-opus-microservices/  # Transformed
│   │   └── claude-haiku-microservices/ # Transformed
│   ├── serverless/
│   │   ├── claude-opus/              # 21 Python files
│   │   ├── claude-haiku/             # 17 Python files
│   │   └── openai-gpt4/              # 17 Python files
│   ├── event-driven/
│   │   ├── claude-opus/main.py       # 547 lines
│   │   ├── claude-haiku/main.py      # 235 lines
│   │   └── openai-gpt4/main.py       # 101 lines
│   └── hexagonal/
│       ├── claude-opus/              # 42 Python files
│       ├── claude-haiku/             # 29 Python files
│       └── openai-gpt4/              # 27 Python files
├── ecommerce/
│   └── monolithic/
│       ├── claude-opus/main.py       # 513 lines
│       ├── claude-haiku/main.py      # 387 lines
│       └── openai-gpt4/main.py       # 55 lines
└── *.md                              # Report files
```

### Research Summary

**20 Experiments Conducted:**
- 3 AI Models: Claude Opus 4.5, Claude 3.5 Haiku, OpenAI GPT-4o
- 5 Architectures: Monolithic, Microservices, Serverless, Event-Driven, Hexagonal
- 2 Applications: Calculator (simple), E-commerce (complex)
- **95% Success Rate** (19/20 experiments)

**Key Findings:**

| Model | Code Quality | Speed | Best For |
|-------|--------------|-------|----------|
| Claude Opus | Production-ready, comprehensive | Slower | Production code |
| Claude Haiku | Good, simpler | 3x faster | Prototyping |
| OpenAI GPT-4o | Minimal, functional | Fast | Simple tasks |

### Running Your Own Experiments

```bash
# Generate with different models
archai -p claude-cli -m opus
> create a monolithic calculator at ./experiments/my-calc

# Transform architecture
> rewrite ./experiments/my-calc to microservices at ./experiments/my-calc-micro

# Try different architectures
> create a hexagonal calculator at ./experiments/my-hex-calc
```

---

## Project Structure

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed file descriptions.

```
archai/
├── archai/                    # Main package
│   ├── __init__.py
│   ├── __main__.py           # Entry point (python -m archai)
│   ├── ai/                   # AI provider implementations
│   ├── architects/           # Architecture generators
│   ├── transformers/         # Code transformation logic
│   ├── cli/                  # CLI interface
│   ├── config/               # Configuration management
│   └── utils/                # Utilities
├── experiments/              # Research experiments
├── tests/                    # Test suite
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── ARCHITECTURE.md          # Codebase documentation
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black archai/
ruff check archai/

# Type checking
mypy archai/
```