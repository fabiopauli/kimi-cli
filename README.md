# Kimi CLI

A powerful command-line AI assistant with support for 6 different language models via Groq API. Built with modular architecture, it features intelligent context management, secure tool execution, model switching, and a rich console interface. Perfect for software development tasks from simple queries to complex multi-file projects.

## Features

- **Multi-Model Support**: Choose from 6 powerful AI models via Groq API:
  - **Kimi-K2-Instruct** (262K context): Default model with massive context window for complex projects
  - **GPT-OSS-120B** (131K context): Reasoner model with built-in reasoning, browser search, and code execution
  - **GPT-OSS-20B** (131K context): Faster alternative with strong performance
  - **Llama-3.3-70B** (131K context): Meta's latest Llama model
  - **Llama-3.1-8B** (131K context): Lightweight and fast
  - **Groq Compound** (131K context): Intelligent tool usage with web search and code execution
- **Model Switching**: Easily switch between models with `/model` and `/reasoner` commands
- **Intelligent File Operations**: Read, create, and edit files with optional fuzzy matching
- **Secure Shell Execution**: Cross-platform shell commands with user confirmation
- **Smart Context Management**: Automatic conversation truncation with token estimation
- **Rich Console Interface**: Beautiful formatting with syntax highlighting
- **Modular Architecture**: Clean separation of concerns with dependency injection
- **Comprehensive Testing**: Full test suite with pytest

## Model Selection Guide

Kimi CLI supports multiple AI models, each optimized for different use cases:

| Model | Context | Best For | Special Features |
|-------|---------|----------|------------------|
| **Kimi-K2-Instruct** | 262K | Large codebases, extensive context | Massive context window for complex projects |
| **GPT-OSS-120B** | 131K | Complex reasoning tasks | Built-in reasoning, browser search, code execution |
| **GPT-OSS-20B** | 131K | General development, speed | Fast responses with strong capabilities |
| **Llama-3.3-70B** | 131K | General purpose | Meta's latest, well-balanced performance |
| **Llama-3.1-8B** | 131K | Quick tasks, low latency | Lightweight and fast |
| **Groq Compound** | 131K | Tasks requiring web search | Intelligent built-in tool usage |

**Quick Start Tips:**
- Use **Kimi-K2** (default) for working with large projects
- Switch to **GPT-OSS-120B** (via `/reasoner`) for complex problem-solving
- Try **Llama-3.3-70B** for a balanced alternative
- Use **Llama-3.1-8B** when speed is critical

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Groq API key

## Installation

### Option 1: Using uv (Recommended)

1. **Install uv** (if not already installed):
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/fabiopauli/kimi-cli.git
   cd kimi-cli
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Set up your API key**:
   ```bash
   # Create a .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   
   # Or export as environment variable
   export GROQ_API_KEY=your_groq_api_key_here
   ```

### Option 2: Using pip

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fabiopauli/kimi-cli.git
   cd kimi-cli
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**:
   ```bash
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

## Usage

### Basic Usage

Start the interactive assistant:

```bash
# Using uv
uv run main.py

# Using python directly
python main.py
```

### Available Commands

#### File & Context Management
- `/add <file_pattern>` - Add files to conversation context with fuzzy matching
- `/remove <file_pattern>` - Remove files from conversation context
- `/folder <path>` - Change working directory
- `/context` - Show current conversation context and token usage
- `/export` - Export current conversation log to a file
- `/clear` - Clear conversation history

#### Model Management
- `/model` - Show current model and list all available models
- `/model <name>` - Switch to a specific model (e.g., `/model llama-3.3-70b-versatile`)
- `/reasoner` - Toggle between default model and reasoner model (GPT-OSS-120B)

#### Settings & System
- `/fuzzy` - Toggle fuzzy file/code matching for current session
- `/os` - Show OS and environment information
- `/cls` - Clear screen
- `/help` - Show available commands
- `/exit` or `/quit` - Exit the application

### Example Session

```bash
$ uv run main.py
┌────────────────────────────────────────────────────────────────┐
│                     Kimi CLI Assistant                         │
├────────────────────────────────────────────────────────────────┤
│ Kimi CLI Assistant - Your AI-powered development companion    │
│                                                                │
│ Type your questions naturally, use /help for commands,        │
│ or /exit to quit. Use /add <file> to include files in        │
│ context, /export to save conversation log.                    │
└────────────────────────────────────────────────────────────────┘

Kimi CLI - User msg: /model
Current Model: moonshotai/kimi-k2-instruct-0905
Context Limit: 262,144 tokens

Available Models:
┌─────────────────────────────────────┬────────────────┬──────────┐
│ Model                               │ Context Tokens │ Role     │
├─────────────────────────────────────┼────────────────┼──────────┤
│ moonshotai/kimi-k2-instruct-0905   │ 262,144        │ Default  │
│ openai/gpt-oss-120b                │ 131,072        │ Reasoner │
│ llama-3.3-70b-versatile            │ 131,072        │          │
└─────────────────────────────────────┴────────────────┴──────────┘

Kimi CLI - User msg: /add src/core/*.py
✓ Added file to context: 'src/core/config.py'
✓ Added file to context: 'src/core/session.py'

Kimi CLI - User msg: explain the configuration system
Kimi CLI - assistant msg: The configuration system is built around a dataclass-based approach...

Kimi CLI - User msg: /reasoner
✓ Switched to reasoner model: openai/gpt-oss-120b
Reasoner model features: reasoning capabilities, browser search, and code execution

Kimi CLI - User msg: /context
📊 Context Usage Statistics
┌────────────────────┬─────────────┐
│ Metric             │ Value       │
├────────────────────┼─────────────┤
│ Model              │ gpt-oss-120b│
│ Estimated Tokens   │ 45,320      │
│ Usage %            │ 34.6%       │
│ Status             │ 🟢 Normal   │
└────────────────────┴─────────────┘
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Optional Configuration File

Create `config.json` for advanced settings:

```json
{
  "models": {
    "default_model": "moonshotai/kimi-k2-instruct-0905",
    "reasoner_model": "openai/gpt-oss-120b"
  },
  "conversation": {
    "max_history_messages": 150,
    "max_context_files": 12,
    "max_reasoning_steps": 10,
    "estimated_max_tokens": 120000,
    "context_warning_threshold": 0.7,
    "aggressive_truncation_threshold": 0.85
  },
  "fuzzy_matching": {
    "enabled_by_default": false,
    "min_fuzzy_score": 80,
    "min_edit_score": 85
  },
  "file_limits": {
    "max_files_in_add_dir": 1000,
    "max_file_size_in_add_dir": 5000000,
    "max_file_content_size_create": 5000000,
    "max_multiple_read_size": 100000
  },
  "security": {
    "require_powershell_confirmation": true,
    "require_bash_confirmation": true
  }
}
```

**Supported Models** (choose any for `default_model` or `reasoner_model`):
- `moonshotai/kimi-k2-instruct-0905` - 262K context (default)
- `openai/gpt-oss-120b` - 131K context with reasoning and tools
- `openai/gpt-oss-20b` - 131K context, faster
- `llama-3.3-70b-versatile` - 131K context
- `llama-3.1-8b-instant` - 131K context, lightweight
- `groq/compound` - 131K context with intelligent tool usage

## Development

### Running Tests

```bash
# Using uv
uv run pytest

# Using pytest directly
pytest
```

### Project Structure

```
kimi-cli/
├── main.py              # Application entry point
├── src/
│   ├── core/            # Core functionality
│   │   ├── config.py    # Configuration management
│   │   └── session.py   # Session and context management
│   ├── commands/        # Special command handlers
│   │   ├── context_commands.py  # Context and model switching
│   │   ├── file_commands.py     # File operations
│   │   └── system_commands.py   # System commands
│   ├── tools/           # AI function calling tools
│   │   ├── file_tools.py        # File operation tools
│   │   └── shell_tools.py       # Shell execution tools
│   ├── ui/              # Console interface
│   └── utils/           # Utility functions
├── tests/               # Comprehensive test suite
├── pyproject.toml       # Project configuration
├── requirements.txt     # Pip dependencies
└── CLAUDE.md           # Development instructions
```

### Architecture Principles

1. **Dependency Injection**: Configuration passed to all components
2. **Modular Design**: Clear separation of concerns
3. **Security-First**: Shell commands require confirmation, fuzzy matching opt-in
4. **Context Management**: Intelligent conversation truncation with token estimation
5. **Cross-Platform**: Works on Windows, macOS, and Linux

## Security Features

- **Shell Command Confirmation**: All shell operations require user approval
- **Path Validation**: Robust file path sanitization
- **File Size Limits**: Configurable limits for file operations
- **Exclusion Patterns**: Automatically excludes system files, node_modules, etc.
- **Fuzzy Matching**: Opt-in only for security (use `/fuzzy` command)

## API Key Setup

Get your Groq API key from [console.groq.com](https://console.groq.com) and either:

1. Add it to your `.env` file: `GROQ_API_KEY=your_key_here`
2. Export as environment variable: `export GROQ_API_KEY=your_key_here`
3. Pass it when running: `GROQ_API_KEY=your_key_here uv run main.py`

## Recent Updates

### Latest Features
- **Multi-Model Support**: Added support for 6 different AI models via Groq API
- **Model Switching**: New `/model` and `/reasoner` commands for easy model switching
- **Enhanced Models**:
  - Kimi-K2-Instruct with 262K context window
  - GPT-OSS-120B reasoner with built-in reasoning and tools
  - Llama-3.3-70B and Llama-3.1-8B models
  - Groq Compound with intelligent tool usage
- **Improved Command Organization**: Commands now organized into logical categories
- **Better Context Management**: Enhanced token estimation and context warnings

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `uv run pytest`
5. Submit a pull request

## License

[License information - check LICENSE file]

## Support

For issues and questions, please open an issue on the [GitHub repository](https://github.com/fabiopauli/kimi-cli/issues).