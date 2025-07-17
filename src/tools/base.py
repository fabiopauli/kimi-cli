#!/usr/bin/env python3

"""
Base tool handler for Kimi Assistant

Provides the foundation for implementing tool handlers.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..core.config import Config


class ToolResult:
    """Result of a tool execution."""
    
    def __init__(self, success: bool, result: str, error: Optional[str] = None):
        self.success = success
        self.result = result
        self.error = error
    
    @classmethod
    def success(cls, result: str) -> 'ToolResult':
        """Create a successful result."""
        return cls(success=True, result=result)
    
    @classmethod
    def error(cls, error: str) -> 'ToolResult':
        """Create an error result."""
        return cls(success=False, result=error, error=error)


class BaseTool(ABC):
    """Base class for all tool handlers."""
    
    def __init__(self, config: Config):
        """Initialize the tool handler."""
        self.config = config
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the tool name."""
        pass
    
    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given arguments."""
        pass


class ToolExecutor:
    """Tool execution coordinator."""
    
    def __init__(self, config: Config):
        """Initialize the tool executor."""
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool handler."""
        self.tools[tool.get_name()] = tool
    
    def execute_tool_call(self, tool_call_dict: Dict[str, Any]) -> str:
        """
        Execute a function call from the LLM.
        
        Args:
            tool_call_dict: Dictionary containing function call information
            
        Returns:
            String result of the function execution
        """
        func_name = "unknown_function"
        try:
            func_name = tool_call_dict["function"]["name"]
            arguments = tool_call_dict["function"]["arguments"]
            
            # Handle both string and dict formats for arguments
            if isinstance(arguments, str):
                # Arguments are JSON string - parse them
                args = json.loads(arguments)
            elif isinstance(arguments, dict):
                # Arguments are already parsed - use directly
                args = arguments
            else:
                return f"Error: Unexpected argument format for '{func_name}': {type(arguments)}"
            
            # Find and execute the appropriate tool
            if func_name in self.tools:
                tool = self.tools[func_name]
                result = tool.execute(args)
                return result.result
            else:
                return f"Error: Unknown function '{func_name}'. Available functions: {list(self.tools.keys())}"
                
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in function arguments for '{func_name}': {str(e)}"
        except Exception as e:
            return f"Error executing function '{func_name}': {str(e)}"