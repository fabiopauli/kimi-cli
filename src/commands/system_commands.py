#!/usr/bin/env python3

"""
System commands for Kimi Assistant

Commands that handle system-level operations like exit, clear, help, etc.
"""

import sys
from typing import Dict, Any

from .base import BaseCommand, CommandResult
from ..core.session import KimiSession


class ExitCommand(BaseCommand):
    """Handle /exit and /quit commands."""
    
    def get_pattern(self) -> str:
        return "/exit"
    
    def get_description(self) -> str:
        return "Exit the application (/exit or /quit)"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() in ("/exit", "/quit")
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        console = get_console()
        console.print("[bold blue]👋 Goodbye![/bold blue]")
        sys.exit(0)


class ClearCommand(BaseCommand):
    """Handle /cls command to clear screen."""
    
    def get_pattern(self) -> str:
        return "/cls"
    
    def get_description(self) -> str:
        return "Clear the screen"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/cls"
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        console = get_console()
        console.clear()
        return CommandResult.success()


class HelpCommand(BaseCommand):
    """Handle /help command to show available commands."""
    
    def get_pattern(self) -> str:
        return "/help"
    
    def get_description(self) -> str:
        return "Show available commands and usage information"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/help"
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        from rich.panel import Panel
        
        console = get_console()
        
        help_text = f"""
**Kimi CLI Assistant** - Your AI-powered development companion

**Available Commands:**
• `/add <path>` - Add file/directory to context with fuzzy matching
• `/remove <path>` - Remove file from context
• `/fuzzy` - Toggle fuzzy matching mode (currently: {'enabled' if self.config.fuzzy_enabled_by_default else 'disabled'})
• `/folder <path>` - Change working directory
• `/cls` - Clear screen
• `/clear` - Clear conversation history
• `/context` - Show context usage statistics
• `/export` - Export current conversation log to a file
• `/os` - Show OS and environment information
• `/model` - Show current model and available models
• `/model <name>` - Switch to a specific model
• `/reasoner` - Toggle reasoner model for complex tasks
• `/help` - Show this help message
• `/exit` or `/quit` - Exit the application

**File Operations:**
Kimi can read, create, and edit files through natural conversation. Just describe what you want to do!

**System Commands:**
Use run_bash (Linux/macOS) or run_powershell (Windows) for system operations.

**Model Switching:**
• Use `/model` to see all available models
• Use `/reasoner` to quickly toggle the reasoner model (openai/gpt-oss-120b)
• Use `/model <name>` to switch to any available model

**Security Features:**
• Fuzzy matching is opt-in for security
• Shell commands require confirmation
• Path validation prevents directory traversal

**Tips:**
• Use `/add` to include files in your conversation context
• Try `/fuzzy` to enable more flexible file matching
• Use `/context` to monitor token usage
• Use `/reasoner` for complex reasoning tasks
• Natural language works best - just describe what you need!
"""
        
        console.print(Panel(help_text, title="Kimi CLI Assistant Help", border_style="bright_blue"))
        return CommandResult.success()


class OsCommand(BaseCommand):
    """Handle /os command to show OS information."""
    
    def get_pattern(self) -> str:
        return "/os"
    
    def get_description(self) -> str:
        return "Show OS and environment information"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/os"
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        from rich.table import Table
        
        console = get_console()
        os_info = self.config.os_info
        
        # Create OS information table
        os_table = Table(title="🖥️ Operating System Information", show_header=True, header_style="bold bright_blue")
        os_table.add_column("Property", style="bright_cyan")
        os_table.add_column("Value", style="white")
        
        os_table.add_row("System", os_info['system'])
        os_table.add_row("Release", os_info['release'])
        os_table.add_row("Version", os_info['version'])
        os_table.add_row("Machine", os_info['machine'])
        os_table.add_row("Processor", os_info['processor'])
        os_table.add_row("Python Version", os_info['python_version'])
        
        console.print(os_table)
        
        # Create shell availability table
        shell_table = Table(title="🐚 Shell Availability", show_header=True, header_style="bold bright_green")
        shell_table.add_column("Shell", style="bright_cyan")
        shell_table.add_column("Available", style="white")
        
        for shell, available in os_info['shell_available'].items():
            status = "✅ Available" if available else "❌ Not Available"
            shell_table.add_row(shell, status)
        
        console.print(shell_table)
        
        # Show current working directory
        console.print(f"\n📁 Current Working Directory: [bright_cyan]{self.config.base_dir}[/bright_cyan]")
        
        return CommandResult.success()


class FuzzyCommand(BaseCommand):
    """Handle /fuzzy command to toggle fuzzy matching."""

    def get_pattern(self) -> str:
        return "/fuzzy"

    def get_description(self) -> str:
        return "Toggle fuzzy matching mode for file operations"

    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/fuzzy"

    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console

        console = get_console()

        if not self.config.fuzzy_available:
            console.print("[bold red]✗[/bold red] Fuzzy matching is not available. Install 'thefuzz' package.")
            return CommandResult.failure("Fuzzy matching not available")

        # Toggle fuzzy mode
        if self.config.fuzzy_enabled_by_default:
            session.disable_fuzzy_mode()
            console.print("[bold green]✓[/bold green] Fuzzy matching disabled for this session.")
        else:
            session.enable_fuzzy_mode()
            console.print("[bold green]✓[/bold green] Fuzzy matching enabled for this session.")

        return CommandResult.success()


class ReasonerCommand(BaseCommand):
    """Handle /reasoner command to switch to reasoner model."""

    def get_pattern(self) -> str:
        return "/reasoner"

    def get_description(self) -> str:
        return "Switch to the reasoner model for complex reasoning tasks"

    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/reasoner"

    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console

        console = get_console()

        # Toggle between reasoner and default model
        if session.model == self.config.reasoner_model:
            # Switch back to default model
            session.switch_model(self.config.default_model)
            console.print(f"[bold green]✓[/bold green] Switched to default model: [bright_cyan]{self.config.default_model}[/bright_cyan]")
        else:
            # Switch to reasoner model
            session.switch_model(self.config.reasoner_model)
            console.print(f"[bold green]✓[/bold green] Switched to reasoner model: [bright_cyan]{self.config.reasoner_model}[/bright_cyan]")
            console.print("[dim]Reasoner model features: reasoning capabilities, browser search, and code execution[/dim]")

        return CommandResult.success()


class ModelCommand(BaseCommand):
    """Handle /model command to show or switch models."""

    def get_pattern(self) -> str:
        return "/model"

    def get_description(self) -> str:
        return "Show current model or switch to a specific model (/model or /model <name>)"

    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower().startswith("/model")

    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        from rich.table import Table

        console = get_console()
        parts = user_input.strip().split(maxsplit=1)

        # If no model name provided, show current model and available models
        if len(parts) == 1:
            # Show current model info
            console.print(f"\n[bold]Current Model:[/bold] [bright_cyan]{session.model}[/bright_cyan]")
            console.print(f"[bold]Context Limit:[/bold] {self.config.get_max_tokens_for_model(session.model):,} tokens\n")

            # Show available models table
            models_table = Table(title="🤖 Available Models", show_header=True, header_style="bold bright_blue")
            models_table.add_column("Model", style="bright_cyan")
            models_table.add_column("Context Tokens", style="white")
            models_table.add_column("Role", style="bright_yellow")

            for model_name, context_limit in self.config.MODEL_CONTEXT_LIMITS.items():
                role = ""
                if model_name == self.config.default_model:
                    role = "Default"
                if model_name == self.config.reasoner_model:
                    role = "Reasoner" if not role else role + ", Reasoner"
                if model_name == session.model:
                    role = "✓ Active" if not role else role + " (✓ Active)"

                models_table.add_row(model_name, f"{context_limit:,}", role)

            console.print(models_table)
            console.print("\n[dim]Use '/model <name>' to switch to a specific model[/dim]")
            console.print("[dim]Use '/reasoner' to quickly toggle the reasoner model[/dim]")

        else:
            # Switch to specified model
            model_name = parts[1].strip()

            # Check if model exists in available models
            if model_name not in self.config.MODEL_CONTEXT_LIMITS:
                console.print(f"[bold red]✗[/bold red] Model '{model_name}' not found.")
                console.print(f"[dim]Available models: {', '.join(self.config.MODEL_CONTEXT_LIMITS.keys())}[/dim]")
                return CommandResult.failure("Model not found")

            # Switch to the model
            session.switch_model(model_name)
            console.print(f"[bold green]✓[/bold green] Switched to model: [bright_cyan]{model_name}[/bright_cyan]")
            console.print(f"[dim]Context limit: {self.config.get_max_tokens_for_model(model_name):,} tokens[/dim]")

        return CommandResult.success()