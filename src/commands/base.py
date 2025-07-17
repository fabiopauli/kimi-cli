#!/usr/bin/env python3

"""
Base command pattern classes for Kimi Assistant

Provides the foundation for implementing commands using the command pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

from ..core.config import Config
from ..core.session import KimiSession


@dataclass
class CommandResult:
    """
    Result of a command execution.
    """
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    should_continue: bool = True  # Whether to continue processing or exit
    
    @classmethod
    def success(cls, message: str = None, data: Any = None, should_continue: bool = True) -> 'CommandResult':
        """Create a successful result."""
        return cls(success=True, message=message, data=data, should_continue=should_continue)
    
    @classmethod
    def failure(cls, message: str, data: Any = None, should_continue: bool = True) -> 'CommandResult':
        """Create a failed result."""
        return cls(success=False, message=message, data=data, should_continue=should_continue)
    
    @classmethod
    def exit(cls, message: str = None) -> 'CommandResult':
        """Create an exit result."""
        return cls(success=True, message=message, should_continue=False)


class BaseCommand(ABC):
    """
    Base class for all commands using the command pattern.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the command.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    @abstractmethod
    def get_pattern(self) -> str:
        """
        Get the command pattern (e.g., "/add", "/remove", "/clear").
        
        Returns:
            Command pattern string
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get a description of what the command does.
        
        Returns:
            Command description
        """
        pass
    
    @abstractmethod
    def execute(self, user_input: str, session: KimiSession) -> CommandResult:
        """
        Execute the command.
        
        Args:
            user_input: The full user input string
            session: Current session
            
        Returns:
            CommandResult indicating success/failure and any data
        """
        pass
    
    def matches(self, user_input: str) -> bool:
        """
        Check if the user input matches this command.
        
        Args:
            user_input: User input string
            
        Returns:
            True if the command matches
        """
        return user_input.strip().startswith(self.get_pattern())
    
    def extract_arguments(self, user_input: str) -> str:
        """
        Extract arguments from user input by removing the command pattern.
        
        Args:
            user_input: Full user input string
            
        Returns:
            Arguments string with command pattern removed
        """
        pattern = self.get_pattern()
        if user_input.strip().startswith(pattern):
            return user_input.strip()[len(pattern):].strip()
        return ""


class CommandRegistry:
    """
    Registry for managing commands using the command pattern.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the command registry.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.commands: List[BaseCommand] = []
    
    def register(self, command: BaseCommand) -> None:
        """
        Register a command.
        
        Args:
            command: Command instance to register
        """
        self.commands.append(command)
    
    def find_command(self, user_input: str) -> Optional[BaseCommand]:
        """
        Find a command that matches the user input.
        
        Args:
            user_input: User input string
            
        Returns:
            Matching command or None
        """
        for command in self.commands:
            if command.matches(user_input):
                return command
        return None
    
    def execute_command(self, user_input: str, session: KimiSession) -> Optional[CommandResult]:
        """
        Execute a command if one matches the user input.
        
        Args:
            user_input: User input string
            session: Current session
            
        Returns:
            CommandResult if command was found and executed, None otherwise
        """
        command = self.find_command(user_input)
        if command:
            return command.execute(user_input, session)
        return None
    
    def get_help_text(self) -> str:
        """
        Get help text for all registered commands.
        
        Returns:
            Formatted help text
        """
        if not self.commands:
            return "No commands available."
        
        help_lines = ["Available commands:"]
        for command in self.commands:
            help_lines.append(f"  {command.get_pattern()} - {command.get_description()}")
        
        return "\n".join(help_lines)