# Kimi CLI

A powerful command-line AI assistant built with modular architecture and Groq's language models. Features intelligent context management, secure tool execution, and a rich console interface.

## Features

- **Kimi-K2 AI Model**: Powered by Moonshot AI's Kimi-K2-Instruct model for enhanced reasoning
- **Intelligent File Operations**: Read, create, and edit files with optional fuzzy matching
- **Secure Shell Execution**: Cross-platform shell commands with user confirmation
- **Smart Context Management**: Automatic conversation truncation with token estimation
- **Rich Console Interface**: Beautiful formatting with syntax highlighting
- **Modular Architecture**: Clean separation of concerns with dependency injection
- **Comprehensive Testing**: Full test suite with pytest

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

- `/add <file_pattern>` - Add files to conversation context with fuzzy matching
- `/remove <file_pattern>` - Remove files from conversation context
- `/context` - Show current conversation context and token usage
- `/export` - Export current conversation log to a file
- `/fuzzy` - Toggle fuzzy file/code matching for current session
- `/folder <path>` - Change working directory
- `/cls` - Clear screen
- `/clear` - Clear conversation history
- `/os` - Show OS and environment information
- `/help` - Show available commands
- `/exit` or `/quit` - Exit the application

### Example Session

```
$ uv run main.py
Kimi CLI Assistant
Powered by Moonshot AI's Kimi-K2-Instruct model

Kimi CLI - User msg: /add src/core/*.py
✓ Added file to context: 'src/core/config.py'
✓ Added file to context: 'src/core/session.py'

Kimi CLI - User msg: explain the configuration system
Kimi CLI - assistant msg: The configuration system is built around a dataclass-based approach...

Kimi CLI - User msg: How can I optimize the token estimation?
Kimi CLI - assistant msg: To optimize token estimation, consider these approaches...
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
    "default_model": "moonshotai/kimi-k2-instruct",
    "reasoner_model": "moonshotai/kimi-k2-instruct"
  },
  "conversation": {
    "max_history_messages": 150,
    "max_context_files": 12,
    "max_reasoning_steps": 10
  },
  "fuzzy_matching": {
    "enabled_by_default": false,
    "min_fuzzy_score": 80,
    "min_edit_score": 85
  },
  "file_limits": {
    "max_files_in_add_dir": 1000,
    "max_file_size_in_add_dir": 5000000,
    "max_file_content_size_create": 5000000
  },
  "security": {
    "require_powershell_confirmation": true,
    "require_bash_confirmation": true
  }
}
```

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