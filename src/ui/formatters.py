#!/usr/bin/env python3

"""
Formatting utilities for Kimi Assistant

Handles formatting of various data types for console display.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


def format_conversation_log(messages: List[Dict[str, Any]], console: Console) -> None:
    """
    Format and display conversation log.
    
    Args:
        messages: List of conversation messages
        console: Rich console instance
    """
    if not messages:
        console.print("[yellow]No messages to display.[/yellow]")
        return
    
    console.print(Panel("📝 Recent Conversation History", border_style="bright_blue"))
    
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        # Handle None content (can occur with tool calls)
        if content is None:
            content = ""
        
        # Format role with color
        if role == "user":
            role_text = Text("👤 User", style="bright_green")
        elif role == "assistant":
            role_text = Text("Assistant", style="bright_blue")
        elif role == "system":
            role_text = Text("⚙️ System", style="bright_yellow")
        else:
            role_text = Text(f"❓ {role}", style="white")
        
        # Handle tool calls in assistant messages
        if role == "assistant" and msg.get("tool_calls"):
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                tool_descriptions = []
                for tool_call in tool_calls:
                    # Handle both dict and ChatCompletionMessageToolCall object formats
                    if hasattr(tool_call, 'function'):
                        # ChatCompletionMessageToolCall object
                        function_name = tool_call.function.name
                    elif isinstance(tool_call, dict):
                        # Dictionary format
                        function_name = tool_call.get("function", {}).get("name", "unknown")
                    else:
                        function_name = "unknown"
                    tool_descriptions.append(f"Used tool: {function_name}")
                content = f"{'; '.join(tool_descriptions)}"
        
        # Truncate long content
        if len(content) > 200:
            content = content[:200] + "..."
        
        console.print(f"{i}. {role_text}")
        console.print(f"   {content}")
        
        if i < len(messages):
            console.print()


def format_file_content(file_path: str, content: str, console: Console, 
                       language: Optional[str] = None) -> None:
    """
    Format and display file content with syntax highlighting.
    
    Args:
        file_path: Path to the file
        content: File content
        console: Rich console instance
        language: Programming language for syntax highlighting
    """
    # Try to detect language from file extension if not provided
    if language is None:
        path = Path(file_path)
        extension = path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.css': 'css',
            '.html': 'html',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.bat': 'batch',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.r': 'r',
            '.m': 'matlab',
            '.tex': 'latex',
            '.dockerfile': 'dockerfile',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
        }
        
        language = language_map.get(extension, 'text')
    
    # Create syntax object
    try:
        syntax = Syntax(content, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"📄 {file_path}", border_style="bright_cyan"))
    except Exception:
        # Fall back to plain text if syntax highlighting fails
        console.print(Panel(content, title=f"📄 {file_path}", border_style="bright_cyan"))


def format_directory_tree(tree_data: Dict[str, Any], console: Console) -> None:
    """
    Format and display directory tree.
    
    Args:
        tree_data: Directory tree data
        console: Rich console instance
    """
    def format_tree_recursive(node: Dict[str, Any], prefix: str = "", is_last: bool = True) -> List[str]:
        """Recursively format tree structure."""
        lines = []
        
        # Current item
        connector = "└── " if is_last else "├── "
        name = node.get("name", "")
        
        if node.get("type") == "directory":
            lines.append(f"{prefix}{connector}📁 {name}/")
            
            # Children
            children = node.get("children", [])
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            for i, child in enumerate(children):
                child_is_last = i == len(children) - 1
                lines.extend(format_tree_recursive(child, child_prefix, child_is_last))
        else:
            lines.append(f"{prefix}{connector}📄 {name}")
        
        return lines
    
    if tree_data:
        tree_lines = format_tree_recursive(tree_data)
        tree_text = "\n".join(tree_lines)
        console.print(tree_text)
    else:
        console.print("[yellow]No directory structure available.[/yellow]")


def format_context_stats(context_info: Dict[str, Any], console: Console) -> None:
    """
    Format and display context statistics.
    
    Args:
        context_info: Context information
        console: Rich console instance
    """
    table = Table(title="📊 Context Statistics", show_header=True, header_style="bold bright_blue")
    table.add_column("Metric", style="bright_cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Model", context_info.get('model', 'Unknown'))
    table.add_row("Messages", str(context_info.get('messages', 0)))
    table.add_row("Estimated Tokens", f"{context_info.get('estimated_tokens', 0):,}")
    table.add_row("Max Tokens", f"{context_info.get('max_tokens', 0):,}")
    table.add_row("Usage %", f"{context_info.get('token_usage_percent', 0):.1f}%")
    
    # Status with color coding
    if context_info.get('critical_limit'):
        status = "[bold red]🔴 Critical[/bold red]"
    elif context_info.get('approaching_limit'):
        status = "[bold yellow]🟡 High[/bold yellow]"
    else:
        status = "[bold green]🟢 Normal[/bold green]"
    
    table.add_row("Status", status)
    
    console.print(table)


def format_tool_result(tool_name: str, result: str, console: Console) -> None:
    """
    Format and display tool execution result.
    
    Args:
        tool_name: Name of the tool
        result: Tool execution result
        console: Rich console instance
    """
    # Try to parse JSON results for better formatting
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            formatted = json.dumps(parsed, indent=2)
            syntax = Syntax(formatted, "json", theme="monokai")
            console.print(Panel(syntax, title=f"🔧 {tool_name} Result", border_style="bright_green"))
            return
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Fall back to plain text
    console.print(Panel(result, title=f"🔧 {tool_name} Result", border_style="bright_green"))


def format_error_message(error: str, console: Console, title: str = "Error") -> None:
    """
    Format and display error message.
    
    Args:
        error: Error message
        console: Rich console instance
        title: Error title
    """
    console.print(Panel(error, title=f"❌ {title}", border_style="bright_red"))


def format_success_message(message: str, console: Console, title: str = "Success") -> None:
    """
    Format and display success message.
    
    Args:
        message: Success message
        console: Rich console instance
        title: Success title
    """
    console.print(Panel(message, title=f"✅ {title}", border_style="bright_green"))


def format_info_message(message: str, console: Console, title: str = "Info") -> None:
    """
    Format and display info message.
    
    Args:
        message: Info message
        console: Rich console instance
        title: Info title
    """
    console.print(Panel(message, title=f"ℹ️ {title}", border_style="bright_blue"))


def format_warning_message(message: str, console: Console, title: str = "Warning") -> None:
    """
    Format and display warning message.
    
    Args:
        message: Warning message
        console: Rich console instance
        title: Warning title
    """
    console.print(Panel(message, title=f"⚠️ {title}", border_style="bright_yellow"))