# Archai - AI Architecture CLI Tool

An interactive CLI tool that uses multiple AI backends to generate and transform software architectures.

---

## Table of Contents

1. [Features](#features)
2. [Supported Architectures](#supported-architectures)
3. [Installation](#installation)
4. [Quick Start](#quick-start)

---

## Features

- **Multiple AI Providers**: Claude CLI, OpenAI, LiteLLM
- **5 Architecture Patterns**: Monolithic, Microservices, Serverless, Event-Driven, Hexagonal
- **Architecture Transformation**: Convert existing codebases between architectures
- **Code Generation**: AI generates complete, runnable code with structure

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
