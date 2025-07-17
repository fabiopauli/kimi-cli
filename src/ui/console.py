#!/usr/bin/env python3

"""
Console interaction module for Kimi Assistant

Handles console output, input, and formatting.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

# Rich console imports
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Prompt toolkit imports
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PromptStyle

# Global console instance
_console = Console()
_prompt_session = PromptSession()


def get_console() -> Console:
    """Get the global console instance."""
    return _console


def get_prompt_session() -> PromptSession:
    """Get the global prompt session instance."""
    return _prompt_session


def initialize_prompt_session() -> None:
    """Initialize the prompt session with proper styling."""
    global _prompt_session
    
    # Define prompt style
    prompt_style = PromptStyle.from_dict({
        'prompt': 'bold blue',
        'input': 'white',
    })
    
    _prompt_session = PromptSession(style=prompt_style)


def get_prompt_indicator(conversation_history: List[Dict[str, Any]], current_model: str) -> str:
    """
    Generate a prompt indicator based on current state.
    
    Args:
        conversation_history: Current conversation history
        current_model: Current model name
        
    Returns:
        Formatted prompt indicator string
    """
    return "Kimi CLI - User msg:"


def display_startup_banner() -> None:
    """Display the startup banner."""
    banner = """
**Kimi CLI Assistant** - Your AI-powered development companion

Type your questions naturally, use /help for commands, or /exit to quit.
Use /add <file> to include files in context, /export to save conversation log.
"""
    _console.print(Panel(banner, title="Kimi CLI Assistant", border_style="bright_blue"))


def display_context_warning(context_info: Dict[str, Any]) -> None:
    """Display context usage warning."""
    if context_info["critical_limit"]:
        _console.print(f"[bold red]⚠ Context Critical: {context_info['token_usage_percent']:.1f}% used[/bold red]")
    elif context_info["approaching_limit"]:
        _console.print(f"[bold yellow]⚠ Context High: {context_info['token_usage_percent']:.1f}% used[/bold yellow]")


def display_model_switch(old_model: str, new_model: str) -> None:
    """Display model switch notification."""
    _console.print(f"[dim]Switched from {old_model} to {new_model}[/dim]")


def display_file_added(file_path: str, file_type: str = "file") -> None:
    """Display file added notification."""
    _console.print(f"[bold green]✓[/bold green] Added {file_type} to context: '[bright_cyan]{file_path}[/bright_cyan]'")


def display_directory_tree(base_dir: Path, tree_summary: str) -> None:
    """Display directory tree summary."""
    _console.print(f"\n📁 Directory: [bright_cyan]{base_dir}[/bright_cyan]")
    _console.print(tree_summary)


def display_error(error_message: str) -> None:
    """Display error message."""
    _console.print(f"[bold red]✗[/bold red] {error_message}")


def display_success(success_message: str) -> None:
    """Display success message."""
    _console.print(f"[bold green]✓[/bold green] {success_message}")


def display_info(info_message: str) -> None:
    """Display info message."""
    _console.print(f"[bold blue]ℹ[/bold blue] {info_message}")


def display_warning(warning_message: str) -> None:
    """Display warning message."""
    _console.print(f"[bold yellow]⚠[/bold yellow] {warning_message}")


def clear_screen() -> None:
    """Clear the console screen."""
    _console.clear()


def display_thinking_indicator() -> None:
    """Display thinking indicator."""
    _console.print("[dim]Thinking...[/dim]")


def display_tool_call(tool_name: str, args: Dict[str, Any]) -> None:
    """Display tool call notification."""
    _console.print(f"[dim]Using tool: {tool_name}[/dim]")


def display_security_confirmation(command: str, command_type: str) -> bool:
    """
    Display security confirmation prompt.
    
    Args:
        command: Command to execute
        command_type: Type of command (bash/powershell)
        
    Returns:
        True if user confirms, False otherwise
    """
    _console.print(f"\n[bold yellow]⚠ Security Confirmation Required[/bold yellow]")
    _console.print(f"[dim]Command type:[/dim] {command_type}")
    _console.print(f"[dim]Command:[/dim] [bright_cyan]{command}[/bright_cyan]")
    
    try:
        response = _prompt_session.prompt("🔐 Execute this command? (y/N): ", default="n")
        return response.strip().lower() in ["y", "yes"]
    except (KeyboardInterrupt, EOFError):
        return False