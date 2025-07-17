"""
Tools module for Kimi Assistant

Contains tool execution handlers for AI function calls.
"""

from .base import BaseTool, ToolResult, ToolExecutor
from .file_tools import create_file_tools
from .shell_tools import create_shell_tools

from ..core.config import Config


def create_tool_executor(config: Config) -> ToolExecutor:
    """
    Create and configure the tool executor with all available tools.
    
    Args:
        config: Configuration object
        
    Returns:
        Configured ToolExecutor instance
    """
    executor = ToolExecutor(config)
    
    # Register file tools
    for tool in create_file_tools(config):
        executor.register_tool(tool)
    
    # Register shell tools
    for tool in create_shell_tools(config):
        executor.register_tool(tool)
    
    return executor


__all__ = [
    'BaseTool',
    'ToolResult',
    'ToolExecutor',
    'create_tool_executor'
]