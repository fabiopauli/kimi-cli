#!/usr/bin/env python3

"""
Session management for Kimi Assistant

Centralizes conversation state and chat instance management with dependency injection.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Third-party imports
from groq import Groq

# Local imports
from .config import Config


class KimiSession:
    """
    Centralized session management for Kimi conversations.
    
    This class encapsulates all conversation state and eliminates the need
    for dual conversation tracking (conversation_history + main_chat).
    Uses dependency injection instead of global state.
    """
    
    def __init__(self, client: Groq, config: Config):
        """
        Initialize a new Kimi session.
        
        Args:
            client: Groq client instance
            config: Configuration object (dependency injection)
        """
        self.client = client
        self.config = config
        self.model = config.current_model
        self.is_reasoner = config.is_reasoner
        self._use_reasoner_next = False
        
        # Initialize conversation history with system prompt
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": self.config.get_system_prompt()}
        ]
        
        # Add initial context
        self._add_initial_context()
    
    def _add_initial_context(self) -> None:
        """Add initial project and environment context to conversation."""
        # Add directory structure
        dir_summary = self._get_directory_tree_summary(self.config.base_dir)
        self.history.append({
            "role": "system",
            "content": f"Project directory structure at startup:\n\n{dir_summary}"
        })
        
        # Add OS and shell info
        shell_status = ", ".join([f"{shell}({'✓' if available else '✗'})" 
                                 for shell, available in self.config.os_info['shell_available'].items()])
        self.history.append({
            "role": "system",
            "content": f"Runtime environment: {self.config.os_info['system']} {self.config.os_info['release']}, "
                      f"Python {self.config.os_info['python_version']}, Shells: {shell_status}"
        })
    
    def _get_directory_tree_summary(self, base_dir: Path) -> str:
        """Get a summary of directory tree structure."""
        # Import here to avoid circular imports
        from ..utils.path_utils import get_directory_tree_summary
        return get_directory_tree_summary(base_dir, self.config)
    
    # Chat instance management methods removed - Groq uses stateless API
    
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role ('user', 'assistant', 'system', 'tool')
            content: Message content
            **kwargs: Additional message properties (e.g., tool_calls, tool_call_id)
        """
        # Create base message without tool_calls to avoid None values
        message = {"role": role, "content": content}
        
        # Add other kwargs except tool_calls (handled separately)
        for key, value in kwargs.items():
            if key != 'tool_calls':
                message[key] = value
        
        # Handle special formatting for assistant messages with tool calls
        if role == 'assistant' and 'tool_calls' in kwargs:
            tool_calls = kwargs['tool_calls']
            if tool_calls is not None:
                message['tool_calls'] = tool_calls
            if not content:  # Groq API requires content to be non-empty string or null
                message['content'] = None
        
        # Handle special formatting for tool messages
        if role == 'tool':
            message = {
                "role": "tool",
                "content": content,
                "tool_call_id": kwargs.get("tool_call_id")
            }
        
        self.history.append(message)
    
    def switch_model(self, new_model: str) -> None:
        """
        Switch to a different model.
        
        Args:
            new_model: Model name to switch to
        """
        if new_model != self.model:
            # Import here to avoid circular imports
            from ..ui.console import get_console
            console = get_console()
            
            console.print(f"[dim]Model changed to {new_model}...[/dim]")
            self.model = new_model
            self.is_reasoner = new_model == self.config.reasoner_model
            self.config.set_model(new_model)
    
    def get_response(self, use_reasoner: bool = False) -> Any:
        """
        Get a response from the current model.
        
        Args:
            use_reasoner: If True, use reasoner model for this response only
        
        Returns:
            Response object from the chat API
        """
        # Check context usage and apply automatic management
        self._manage_context()
        
        # Check if we should use reasoner for this response
        should_use_reasoner = use_reasoner or self._use_reasoner_next
        current_model = self.config.reasoner_model if should_use_reasoner else self.model
        
        # Reset the one-time reasoner flag
        self._use_reasoner_next = False
        
        try:
            # Make API call to Groq with full conversation history
            completion = self.client.chat.completions.create(
                model=current_model,
                messages=self.history,
                tools=self.config.get_tools(),
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096,
                stream=False,
            )
            response = completion.choices[0].message
            
            # Add the assistant's response to history
            self.add_message(
                role='assistant',
                content=response.content,
                tool_calls=response.tool_calls
            )
            
            return response
            
        except Exception as e:
            # Handle potential API errors
            print(f"An error occurred with the Groq API: {e}")
            # Return a mock response to avoid crashes
            from unittest.mock import Mock
            mock_response = Mock()
            mock_response.content = f"Sorry, an API error occurred: {e}"
            mock_response.tool_calls = None
            return mock_response
    
    def _manage_context(self) -> None:
        """Manage context size and apply truncation if needed."""
        # Import here to avoid circular imports
        from ..utils.text_utils import get_context_usage_info, smart_truncate_history
        from ..ui.console import get_console
        
        console = get_console()
        context_info = get_context_usage_info(self.history, self.model, self.config)
        
        # Automatic sliding window management
        if context_info["estimated_tokens"] > context_info["max_tokens"]:
            console.print(f"[red]⚠ Context exceeds limit: {context_info['token_usage_percent']:.1f}% used. Auto-applying sliding window...[/red]")
            self.history = smart_truncate_history(self.history, self.model, self.config)
            
            # Recalculate and report
            context_info = get_context_usage_info(self.history, self.model, self.config)
            console.print(f"[green]✓ Context optimized: {context_info['token_usage_percent']:.1f}% used[/green]")
            
        elif context_info["critical_limit"]:
            console.print(f"[red]⚠ Context critical: {context_info['token_usage_percent']:.1f}% used. Auto-truncating history...[/red]")
            self.history = smart_truncate_history(self.history, self.model, self.config)
            
            # Recalculate and report
            context_info = get_context_usage_info(self.history, self.model, self.config)
            console.print(f"[green]✓ Context optimized: {context_info['token_usage_percent']:.1f}% used[/green]")
            
        elif context_info["approaching_limit"] and len(self.history) % 20 == 0:
            console.print(f"[yellow]⚠ Context high: {context_info['token_usage_percent']:.1f}% used. Use /context for details.[/yellow]")
    
    def update_working_directory(self, new_base_dir: Path) -> None:
        """
        Update the working directory context and refresh system prompt.
        
        Args:
            new_base_dir: New base directory path
        """
        # Update config with new base directory
        self.config.set_base_dir(new_base_dir)
        
        # Update the system prompt with new working directory context
        new_system_prompt = self.config.get_system_prompt()
        
        # Update the first message (system prompt) in history
        if self.history and self.history[0]["role"] == "system":
            self.history[0]["content"] = new_system_prompt
        
        # Add directory change notification to conversation context
        dir_summary = self._get_directory_tree_summary(new_base_dir)
        self.add_message("system", f"Working directory changed to: {new_base_dir}\n\nNew directory structure:\n\n{dir_summary}")
    
    def clear_context(self, keep_system_prompt: bool = True) -> None:
        """
        Clear conversation context.
        
        Args:
            keep_system_prompt: Whether to keep the system prompt
        """
        if keep_system_prompt and self.history:
            # Keep system prompt and rebuild with fresh context
            original_system_prompt = self.history[0]
            self.history = [original_system_prompt]
            self._add_initial_context()
        else:
            # Complete clear
            self.history = []
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get current context usage information."""
        from ..utils.text_utils import get_context_usage_info
        return get_context_usage_info(self.history, self.model, self.config)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get a copy of the conversation history."""
        return self.history.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return {
            "current_model": self.model,
            "is_reasoner": self.is_reasoner,
            "model_name": self.model
        }
    
    def enable_fuzzy_mode(self) -> None:
        """Enable fuzzy matching for the current session."""
        self.config.fuzzy_enabled_by_default = True
        self.add_message("system", "Fuzzy matching enabled for file operations in this session.")
    
    def disable_fuzzy_mode(self) -> None:
        """Disable fuzzy matching for the current session."""
        self.config.fuzzy_enabled_by_default = False
        self.add_message("system", "Fuzzy matching disabled for file operations in this session.")