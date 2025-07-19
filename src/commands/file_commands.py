#!/usr/bin/env python3

"""
File operation commands for Kimi Assistant

Commands that handle file operations like add, remove, folder changes, etc.
"""

from pathlib import Path
from typing import Optional

from .base import BaseCommand, CommandResult
from ..core.session import KimiSession


class AddCommand(BaseCommand):
    """Handle /add command with fuzzy file finding support."""
    
    def get_pattern(self) -> str:
        return "/add "
    
    def get_description(self) -> str:
        return "Add file/directory to context with fuzzy matching"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower().startswith(self.config.ADD_COMMAND_PREFIX)
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console, get_prompt_session
        from ..utils.file_utils import find_best_matching_file, add_file_context_smartly
        
        console = get_console()
        prompt_session = get_prompt_session()
        
        path_to_add = user_input[len(self.config.ADD_COMMAND_PREFIX):].strip()
        
        # 1. Try direct path first
        try:
            p = (self.config.base_dir / path_to_add).resolve()
            if p.exists():
                normalized_path = str(p)
            else:
                # This will raise an error if it doesn't exist, triggering the fuzzy search
                _ = p.resolve(strict=True) 
        except (FileNotFoundError, OSError):
            # 2. If direct path fails, try fuzzy finding
            console.print(f"[dim]Path '{path_to_add}' not found directly, attempting fuzzy search...[/dim]")
            fuzzy_match = find_best_matching_file(self.config.base_dir, path_to_add, self.config)

            if fuzzy_match:
                # Optional: Confirm with user for better UX
                relative_fuzzy = Path(fuzzy_match).relative_to(self.config.base_dir)
                confirm = prompt_session.prompt(f"🔵 Did you mean '[bright_cyan]{relative_fuzzy}[/bright_cyan]'? (Y/n): ", default="y").strip().lower()
                if confirm in ["y", "yes"]:
                    normalized_path = fuzzy_match
                else:
                    console.print("[yellow]Add command cancelled.[/yellow]")
                    return CommandResult.success()
            else:
                console.print(f"[bold red]✗[/bold red] Path does not exist: '[bright_cyan]{path_to_add}[/bright_cyan]'")
                if self.config.fuzzy_available:
                    console.print("[dim]💡 Tip: Make sure the path is correct. Fuzzy matching is enabled.[/dim]")
                else:
                    console.print("[dim]💡 Tip: Install 'thefuzz' for fuzzy path matching support.[/dim]")
                return CommandResult.failure("Path not found")
        
        # 3. Add to context
        try:
            add_file_context_smartly(normalized_path, session, self.config)
            return CommandResult.success()
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Error adding file: {e}")
            return CommandResult.failure(str(e))


class RemoveCommand(BaseCommand):
    """Handle /remove command to remove files from context."""
    
    def get_pattern(self) -> str:
        return "/remove "
    
    def get_description(self) -> str:
        return "Remove file from context"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower().startswith("/remove ")
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        from ..utils.file_utils import find_best_matching_file
        
        console = get_console()
        path_to_remove = user_input[len("/remove "):].strip()
        
        # Try direct path first
        try:
            p = (self.config.base_dir / path_to_remove).resolve()
            if p.exists():
                normalized_path = str(p)
            else:
                # Try fuzzy finding
                fuzzy_match = find_best_matching_file(self.config.base_dir, path_to_remove, self.config)
                if fuzzy_match:
                    normalized_path = fuzzy_match
                else:
                    console.print(f"[bold red]✗[/bold red] Path does not exist: '[bright_cyan]{path_to_remove}[/bright_cyan]'")
                    return CommandResult.failure("Path not found")
        except (FileNotFoundError, OSError):
            console.print(f"[bold red]✗[/bold red] Path does not exist: '[bright_cyan]{path_to_remove}[/bright_cyan]'")
            return CommandResult.failure("Path not found")
        
        # Remove from context
        conversation_history = session.get_conversation_history()
        
        # Find and remove matching context entries
        relative_path = Path(normalized_path).relative_to(self.config.base_dir)
        removed_count = 0
        
        # Filter out messages that contain the file path
        filtered_history = []
        for msg in conversation_history:
            if (msg["role"] == "system" and 
                "User added file" in msg["content"] and 
                str(relative_path) in msg["content"]):
                removed_count += 1
                continue
            filtered_history.append(msg)
        
        if removed_count > 0:
            # Update session history
            session.history = filtered_history
            
            console.print(f"[bold green]✓[/bold green] Removed '[bright_cyan]{relative_path}[/bright_cyan]' from context")
            return CommandResult.success()
        else:
            console.print(f"[bold yellow]⚠[/bold yellow] '[bright_cyan]{relative_path}[/bright_cyan]' not found in context")
            return CommandResult.success()


class FolderCommand(BaseCommand):
    """Handle /folder command to change working directory."""
    
    def get_pattern(self) -> str:
        return "/folder "
    
    def get_description(self) -> str:
        return "Change working directory or show current directory structure"
    
    def matches(self, user_input: str) -> bool:
        return user_input.strip().lower().startswith("/folder")
    
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        from ..ui.console import get_console
        
        console = get_console()
        user_input_stripped = user_input.strip().lower()
        
        # Check if it's just /folder without any path (fallback mode)
        if user_input_stripped == "/folder":
            return self._show_current_directory_structure(console)
        
        # Extract folder path (handle both "/folder " and "/folder" followed by path)
        if user_input_stripped.startswith("/folder "):
            folder_path = user_input[len("/folder "):].strip()
        else:
            folder_path = user_input[len("/folder"):].strip()
        
        # If no path provided after extraction, show current directory
        if not folder_path:
            return self._show_current_directory_structure(console)
        
        # Handle special cases
        if folder_path == "..":
            new_path = self.config.base_dir.parent
        elif folder_path == ".":
            new_path = self.config.base_dir
        elif folder_path.startswith("~"):
            new_path = Path(folder_path).expanduser()
        else:
            # Try relative to current directory first
            if Path(folder_path).is_absolute():
                new_path = Path(folder_path)
            else:
                new_path = self.config.base_dir / folder_path
        
        # Validate path
        try:
            new_path = new_path.resolve()
            if not new_path.exists():
                console.print(f"[bold red]✗[/bold red] Directory does not exist: '[bright_cyan]{new_path}[/bright_cyan]'")
                return CommandResult.failure("Directory not found")
            
            if not new_path.is_dir():
                console.print(f"[bold red]✗[/bold red] Path is not a directory: '[bright_cyan]{new_path}[/bright_cyan]'")
                return CommandResult.failure("Path is not a directory")
        except (FileNotFoundError, OSError, PermissionError) as e:
            console.print(f"[bold red]✗[/bold red] Error accessing directory: {e}")
            return CommandResult.failure(str(e))
        
        # Update working directory
        old_path = self.config.base_dir
        session.update_working_directory(new_path)
        
        console.print(f"[bold green]✓[/bold green] Changed working directory")
        console.print(f"[dim]From:[/dim] [bright_cyan]{old_path}[/bright_cyan]")
        console.print(f"[dim]To:[/dim] [bright_cyan]{new_path}[/bright_cyan]")
        
        return CommandResult.success()
    
    def _show_current_directory_structure(self, console) -> CommandResult:
        """Show the structure of the current working directory (non-recursive)."""
        try:
            current_dir = self.config.base_dir
            console.print(f"[bold green]📁[/bold green] Current directory: [bright_cyan]{current_dir}[/bright_cyan]")
            console.print()
            
            # Get directory contents
            items = []
            try:
                for item in current_dir.iterdir():
                    if item.is_dir():
                        items.append((item.name, "📁", "directory"))
                    else:
                        items.append((item.name, "📄", "file"))
            except PermissionError:
                console.print(f"[bold red]✗[/bold red] Permission denied accessing directory contents")
                return CommandResult.failure("Permission denied")
            
            # Sort items: directories first, then files, both alphabetically
            items.sort(key=lambda x: (x[2] == "file", x[0].lower()))
            
            if not items:
                console.print(f"[dim]Directory is empty[/dim]")
            else:
                console.print(f"[dim]Contents ({len(items)} items):[/dim]")
                for name, icon, item_type in items:
                    console.print(f"  {icon} {name}")
                    
                # Summary
                dirs = sum(1 for _, _, item_type in items if item_type == "directory")
                files = sum(1 for _, _, item_type in items if item_type == "file")
                console.print()
                console.print(f"[dim]{dirs} director{'y' if dirs == 1 else 'ies'}, {files} file{'s' if files != 1 else ''}[/dim]")
            
            return CommandResult.success()
            
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Error reading directory: {e}")
            return CommandResult.failure(str(e))