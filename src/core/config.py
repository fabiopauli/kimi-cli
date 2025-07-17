#!/usr/bin/env python3

"""
Configuration management for Kimi Assistant

This module provides a Config class that eliminates global state
and provides dependency injection for configuration values.
"""

import os
import json
import platform
from pathlib import Path
from typing import Dict, Any, Set, Optional
from dataclasses import dataclass, field
# Removed xAI SDK import - now using Groq JSON schema format


@dataclass
class Config:
    """
    Configuration class that encapsulates all application settings
    and eliminates global state dependencies.
    """
    
    # Core paths
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    config_file: Optional[Path] = None
    
    # Model settings
    default_model: str = "moonshotai/kimi-k2-instruct"
    reasoner_model: str = "moonshotai/kimi-k2-instruct"
    current_model: str = "moonshotai/kimi-k2-instruct"
    is_reasoner: bool = False
    
    # File limits
    max_files_in_add_dir: int = 1000
    max_file_size_in_add_dir: int = 5_000_000
    max_file_content_size_create: int = 5_000_000
    max_multiple_read_size: int = 100_000
    
    # Fuzzy matching settings
    min_fuzzy_score: int = 80
    min_edit_score: int = 85
    fuzzy_enabled_by_default: bool = False  # Security improvement: opt-in fuzzy matching
    
    # Conversation settings
    max_history_messages: int = 150
    max_context_files: int = 12
    estimated_max_tokens: int = 120000
    max_reasoning_steps: int = 10
    context_warning_threshold: float = 0.7
    aggressive_truncation_threshold: float = 0.85
    
    # Security settings
    require_powershell_confirmation: bool = True
    require_bash_confirmation: bool = True
    
    # Git context
    git_enabled: bool = False
    git_skip_staging: bool = False
    git_branch: Optional[str] = None
    
    # OS information
    os_info: Dict[str, Any] = field(default_factory=dict)
    
    # File exclusions
    excluded_files: Set[str] = field(default_factory=set)
    excluded_extensions: Set[str] = field(default_factory=set)
    
    # Constants
    ADD_COMMAND_PREFIX: str = "/add "
    MODEL_CONTEXT_LIMITS: Dict[str, int] = field(default_factory=lambda: {
        "llama-3.3-70b-versatile": 131072,
        "moonshotai/kimi-k2-instruct": 131072,
        "llama-3.1-8b-instant": 131072,
        "mixtral-8x7b-32768": 32768,
    })
    
    def __post_init__(self):
        """Initialize configuration after object creation."""
        self._detect_os_info()
        self._load_config_file()
        self._set_default_exclusions()
        self._validate_fuzzy_availability()
    
    def _detect_os_info(self) -> None:
        """Detect OS information and available shells."""
        self.os_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_windows': platform.system() == "Windows",
            'is_mac': platform.system() == "Darwin",
            'is_linux': platform.system() == "Linux",
            'shell_available': {
                'bash': False,
                'powershell': False,
                'zsh': False,
                'cmd': False
            }
        }
        
        # Detect available shells
        self._detect_available_shells()
    
    def _detect_available_shells(self) -> None:
        """Detect which shells are available on the system."""
        import shutil
        
        shells = ['bash', 'zsh', 'powershell', 'cmd']
        for shell in shells:
            if shell == 'cmd' and self.os_info['is_windows']:
                # cmd is always available on Windows
                self.os_info['shell_available'][shell] = True
            elif shell == 'powershell':
                # Check for both Windows PowerShell and PowerShell Core
                self.os_info['shell_available'][shell] = (
                    shutil.which('powershell') is not None or 
                    shutil.which('pwsh') is not None
                )
            else:
                self.os_info['shell_available'][shell] = shutil.which(shell) is not None
    
    def _load_config_file(self) -> None:
        """Load configuration from config.json file."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._apply_config_data(config_data)
                    self.config_file = config_path
        except (FileNotFoundError, json.JSONDecodeError):
            # Use defaults if config file doesn't exist or is invalid
            pass
    
    def _apply_config_data(self, config_data: Dict[str, Any]) -> None:
        """Apply configuration data from file."""
        # File limits
        if 'file_limits' in config_data:
            file_limits = config_data['file_limits']
            self.max_files_in_add_dir = file_limits.get('max_files_in_add_dir', self.max_files_in_add_dir)
            self.max_file_size_in_add_dir = file_limits.get('max_file_size_in_add_dir', self.max_file_size_in_add_dir)
            self.max_file_content_size_create = file_limits.get('max_file_content_size_create', self.max_file_content_size_create)
            self.max_multiple_read_size = file_limits.get('max_multiple_read_size', self.max_multiple_read_size)
        
        # Fuzzy matching
        if 'fuzzy_matching' in config_data:
            fuzzy_config = config_data['fuzzy_matching']
            self.min_fuzzy_score = fuzzy_config.get('min_fuzzy_score', self.min_fuzzy_score)
            self.min_edit_score = fuzzy_config.get('min_edit_score', self.min_edit_score)
            self.fuzzy_enabled_by_default = fuzzy_config.get('enabled_by_default', self.fuzzy_enabled_by_default)
        
        # Conversation settings
        if 'conversation' in config_data:
            conv_config = config_data['conversation']
            self.max_history_messages = conv_config.get('max_history_messages', self.max_history_messages)
            self.max_context_files = conv_config.get('max_context_files', self.max_context_files)
            self.estimated_max_tokens = conv_config.get('estimated_max_tokens', self.estimated_max_tokens)
            self.max_reasoning_steps = conv_config.get('max_reasoning_steps', self.max_reasoning_steps)
            self.context_warning_threshold = conv_config.get('context_warning_threshold', self.context_warning_threshold)
            self.aggressive_truncation_threshold = conv_config.get('aggressive_truncation_threshold', self.aggressive_truncation_threshold)
        
        # Models
        if 'models' in config_data:
            model_config = config_data['models']
            self.default_model = model_config.get('default_model', self.default_model)
            self.reasoner_model = model_config.get('reasoner_model', self.reasoner_model)
            self.current_model = self.default_model
        
        # Security
        if 'security' in config_data:
            security_config = config_data['security']
            self.require_powershell_confirmation = security_config.get('require_powershell_confirmation', self.require_powershell_confirmation)
            self.require_bash_confirmation = security_config.get('require_bash_confirmation', self.require_bash_confirmation)
        
        # File exclusions
        if 'excluded_files' in config_data:
            self.excluded_files.update(config_data['excluded_files'])
        
        if 'excluded_extensions' in config_data:
            self.excluded_extensions.update(config_data['excluded_extensions'])
    
    def _set_default_exclusions(self) -> None:
        """Set default file and extension exclusions."""
        if not self.excluded_files:
            self.excluded_files = {
                ".DS_Store", "Thumbs.db", ".gitignore", ".python-version", "uv.lock", 
                ".uv", "uvenv", ".uvenv", ".venv", "venv", "__pycache__", ".pytest_cache", 
                ".coverage", ".mypy_cache", "node_modules", "package-lock.json", "yarn.lock", 
                "pnpm-lock.yaml", ".next", ".nuxt", "dist", "build", ".cache", ".parcel-cache", 
                ".turbo", ".vercel", ".output", ".contentlayer", "out", "coverage", 
                ".nyc_output", "storybook-static", ".env", ".env.local", ".env.development", 
                ".env.production", ".git", ".svn", ".hg", "CVS"
            }
        
        if not self.excluded_extensions:
            self.excluded_extensions = {
                ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".avif", 
                ".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg", ".zip", ".tar", 
                ".gz", ".7z", ".rar", ".exe", ".dll", ".so", ".dylib", ".bin", 
                ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pyc", 
                ".pyo", ".pyd", ".egg", ".whl", ".uv", ".uvenv", ".db", ".sqlite", 
                ".sqlite3", ".log", ".idea", ".vscode", ".map", ".chunk.js", 
                ".chunk.css", ".min.js", ".min.css", ".bundle.js", ".bundle.css", 
                ".cache", ".tmp", ".temp", ".ttf", ".otf", ".woff", ".woff2", ".eot"
            }
    
    def _validate_fuzzy_availability(self) -> None:
        """Check if fuzzy matching is available."""
        try:
            from thefuzz import fuzz, process as fuzzy_process
            self.fuzzy_available = True
        except ImportError:
            self.fuzzy_available = False
            self.fuzzy_enabled_by_default = False
    
    def get_max_tokens_for_model(self, model_name: Optional[str] = None) -> int:
        """Get the maximum context tokens for a specific model."""
        if model_name is None:
            model_name = self.current_model
        return self.MODEL_CONTEXT_LIMITS.get(model_name, 128000)
    
    def set_base_dir(self, path: Path) -> None:
        """Set the base directory for operations."""
        self.base_dir = path.resolve()
    
    def set_model(self, model_name: str) -> None:
        """Set the current model."""
        self.current_model = model_name
        self.is_reasoner = model_name == self.reasoner_model
    
    def enable_git(self, branch: Optional[str] = None, skip_staging: bool = False) -> None:
        """Enable git context."""
        self.git_enabled = True
        self.git_branch = branch
        self.git_skip_staging = skip_staging
    
    def disable_git(self) -> None:
        """Disable git context."""
        self.git_enabled = False
        self.git_branch = None
        self.git_skip_staging = False
    
    def get_system_prompt(self) -> str:
        """Get the formatted system prompt."""
        return self._load_and_format_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from external file."""
        try:
            prompt_path = Path(__file__).parent.parent.parent / "system_prompt.txt"
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except (FileNotFoundError, IOError):
            pass
        return self._get_default_system_prompt()
    
    def _load_and_format_system_prompt(self) -> str:
        """Load and format the system prompt with current environment info."""
        prompt_template = self._load_system_prompt()
        
        # Build shell availability string
        available_shells = [shell for shell, available in self.os_info['shell_available'].items() if available]
        shells_str = ', '.join(available_shells) if available_shells else 'None'
        
        # Build git status string
        git_status = 'Not detected'
        if self.git_enabled:
            branch = self.git_branch or 'unknown'
            git_status = f'Enabled (branch: {branch})'
        
        # Build context dictionary for template formatting
        format_context = {
            'os_info': self.os_info,
            'current_working_directory': str(self.base_dir),
            'shells_available': shells_str,
            'git_status': git_status
        }
        
        try:
            # Format the template with current context
            formatted_prompt = prompt_template.format(**format_context)
            return formatted_prompt
        except (KeyError, ValueError):
            # If template formatting fails, fall back to original prompt
            return prompt_template
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return f"""
You are an elite software engineer called Kimi Assistant with decades of experience across all programming domains.
Your expertise spans system design, algorithms, testing, and best practices.
You provide thoughtful, well-structured solutions while explaining your reasoning.

**Current Environment:**
- Operating System: {self.os_info['system']} {self.os_info['release']}
- Machine: {self.os_info['machine']}
- Python: {self.os_info['python_version']}

Core capabilities:
1. Code Analysis & Discussion
   - Analyze code with expert-level insight
   - Explain complex concepts clearly
   - Suggest optimizations and best practices
   - Debug issues with precision

2. File Operations (via function calls):
   - read_file: Read a single file's content
   - read_multiple_files: Read multiple files at once (returns structured JSON)
   - create_file: Create or overwrite a single file
   - create_multiple_files: Create multiple files at once
   - edit_file: Make precise edits to existing files (fuzzy matching available with /fuzzy flag)

3. System Operations (with security confirmation):
   - run_powershell: Execute PowerShell commands (Windows/Cross-platform PowerShell Core)
   - run_bash: Execute bash commands (macOS/Linux/WSL)
   
   Note: Choose the appropriate shell command based on the operating system:
   - On Windows: Prefer run_powershell
   - On macOS/Linux: Prefer run_bash
   - Both commands require user confirmation for security
   - You can use these shell commands to perform Git operations (e.g., `git status`, `git commit`).

Guidelines:
1. Provide natural, conversational responses explaining your reasoning
2. Use function calls when you need to read or modify files, or interact with the shell.
3. For file operations:
   - Fuzzy matching is now opt-in for security - use /fuzzy flag when needed
   - Always read files first before editing them to understand the context
   - Explain what changes you're making and why
   - Consider the impact of changes on the overall codebase
4. For system commands:
   - Always consider the operating system when choosing between run_bash and run_powershell
   - Explain what the command does before executing
   - Use safe, non-destructive commands when possible
   - Be cautious with commands that modify system state
5. Follow language-specific best practices
6. Suggest tests or validation steps when appropriate
7. Be thorough in your analysis and recommendations

IMPORTANT: In your thinking process, if you realize that something requires a tool call, cut your thinking short and proceed directly to the tool call. Don't overthink - act efficiently when file operations are needed.

Remember: You're a senior engineer - be thoughtful, precise, and explain your reasoning clearly.
"""
    
    def get_tools(self) -> list:
        """Get the function calling tools definition in JSON schema format for Groq."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the content of a single file from the filesystem",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to read",
                            },
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_multiple_files",
                    "description": "Read the content of multiple files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of file paths to read",
                            },
                        },
                        "required": ["file_paths"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create or overwrite a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path for the file",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content for the file",
                            },
                        },
                        "required": ["file_path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_multiple_files",
                    "description": "Create multiple files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "content": {"type": "string"},
                                    },
                                    "required": ["path", "content"],
                                },
                                "description": "Array of files to create (path, content)",
                            },
                        },
                        "required": ["files"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing a snippet (fuzzy matching available with /fuzzy flag)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file",
                            },
                            "original_snippet": {
                                "type": "string",
                                "description": "Snippet to replace",
                            },
                            "new_snippet": {
                                "type": "string",
                                "description": "Replacement snippet",
                            },
                        },
                        "required": ["file_path", "original_snippet", "new_snippet"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_powershell",
                    "description": "Run a PowerShell command with security confirmation (Windows/Cross-platform PowerShell Core).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The PowerShell command to execute",
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_bash",
                    "description": "Run a bash command with security confirmation (macOS/Linux/WSL).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The bash command to execute",
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
        ]