#!/usr/bin/env python3

"""
Context management commands for Kimi Assistant

Commands that handle conversation context, model switching, etc.
"""

from .base import BaseCommand, CommandResult
from ..core.session import KimiSession


class ClearContextCommand(BaseCommand):
    """Handle /clear context command to clear conversation history."""
    
    def get_pattern(self) -> str:
        return "/clear"
    
    def get_description(self) -> str:
        return "Clear conversation history"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/clear"
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console, get_prompt_session
        
        console = get_console()
        prompt_session = get_prompt_session()
        
        conversation_history = session.get_conversation_history()
        
        if len(conversation_history) <= 1:
            console.print("[yellow]Context already empty (only system prompt).[/yellow]")
            return CommandResult.success()
            
        file_contexts = sum(1 for msg in conversation_history if msg["role"] == "system" and "User added file" in msg["content"])
        total_messages = len(conversation_history) - 1
        
        console.print(f"[yellow]Current context: {total_messages} messages, {file_contexts} file contexts[/yellow]")
        
        # Confirm with user
        confirm = prompt_session.prompt("🔵 Are you sure you want to clear the context? (y/N): ", default="n").strip().lower()
        
        if confirm in ["y", "yes"]:
            session.clear_context(keep_system_prompt=True)
            console.print("[bold green]✓[/bold green] Context cleared (system prompt retained)")
            return CommandResult.success()
        else:
            console.print("[yellow]Context clear cancelled.[/yellow]")
            return CommandResult.success()


class ContextCommand(BaseCommand):
    """Handle /context command to show context usage statistics."""
    
    def get_pattern(self) -> str:
        return "/context"
    
    def get_description(self) -> str:
        return "Show context usage statistics"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/context"
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        from rich.table import Table
        
        console = get_console()
        context_info = session.get_context_info()
        
        context_table = Table(title="📊 Context Usage Statistics", show_header=True, header_style="bold bright_blue")
        context_table.add_column("Metric", style="bright_cyan")
        context_table.add_column("Value", style="white")
        
        context_table.add_row("Model", context_info['model'])
        context_table.add_row("Messages", str(context_info['messages']))
        context_table.add_row("Estimated Tokens", f"{context_info['estimated_tokens']:,}")
        context_table.add_row("Max Tokens", f"{context_info['max_tokens']:,}")
        context_table.add_row("Usage %", f"{context_info['token_usage_percent']:.1f}%")
        
        # Color-code status
        if context_info['critical_limit']:
            status = "[bold red]🔴 Critical[/bold red]"
        elif context_info['approaching_limit']:
            status = "[bold yellow]🟡 High[/bold yellow]"
        else:
            status = "[bold green]🟢 Normal[/bold green]"
        
        context_table.add_row("Status", status)
        
        console.print(context_table)
        
        # Show recommendations
        if context_info['critical_limit']:
            console.print("\n[bold red]⚠ Context is critical![/bold red]")
            console.print("[dim]Consider using /clear context to reduce token usage.[/dim]")
        elif context_info['approaching_limit']:
            console.print("\n[bold yellow]⚠ Context is getting high.[/bold yellow]")
            console.print("[dim]Monitor usage to avoid context limits.[/dim]")
        
        return CommandResult.success()


class ExportCommand(BaseCommand):
    """Handle /export command to export conversation log to a file."""
    
    def get_pattern(self) -> str:
        return "/export"
    
    def get_description(self) -> str:
        return "Export current conversation log to a file"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower() == "/export"
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console, get_prompt_session
        from datetime import datetime
        from pathlib import Path
        import json
        import os
        
        console = get_console()
        prompt_session = get_prompt_session()
        conversation_history = session.get_conversation_history()
        
        if len(conversation_history) <= 1:
            console.print("[yellow]No conversation history available to export.[/yellow]")
            return CommandResult.success()
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        try:
            logs_dir.mkdir(exist_ok=True)
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Error creating logs directory: {str(e)}")
            return CommandResult.failure(str(e))
        
        # Get filename from user
        default_filename = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filename = prompt_session.prompt(f"Enter filename (default: {default_filename}): ", default=default_filename).strip()
        
        if not filename:
            filename = default_filename
        
        # Add .json extension if not present
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Create full path in logs directory
        full_path = logs_dir / filename
        
        try:
            # Filter out system messages for export and convert to JSON-serializable format
            export_messages = []
            for msg in conversation_history:
                if msg["role"] != "system":
                    # Create a clean copy of the message
                    clean_msg = {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                    
                    # Handle tool calls if present
                    if "tool_calls" in msg and msg["tool_calls"]:
                        clean_msg["tool_calls"] = []
                        for tool_call in msg["tool_calls"]:
                            # Convert ChatCompletionMessageToolCall to dict
                            if hasattr(tool_call, 'function'):
                                # It's a ChatCompletionMessageToolCall object
                                clean_tool_call = {
                                    "id": getattr(tool_call, 'id', None),
                                    "type": getattr(tool_call, 'type', 'function'),
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            else:
                                # It's already a dict
                                clean_tool_call = tool_call
                            clean_msg["tool_calls"].append(clean_tool_call)
                    
                    # Handle tool_call_id if present
                    if "tool_call_id" in msg:
                        clean_msg["tool_call_id"] = msg["tool_call_id"]
                    
                    export_messages.append(clean_msg)
            
            # Prepare export data
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_messages": len(export_messages),
                "messages": export_messages
            }
            
            # Write to file
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            console.print(f"[bold green]✓[/bold green] Conversation exported to '[bright_cyan]{full_path}[/bright_cyan]'")
            console.print(f"[dim]Exported {len(export_messages)} messages[/dim]")
            return CommandResult.success()
            
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Error exporting conversation: {str(e)}")
            return CommandResult.failure(str(e))






