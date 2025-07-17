#!/usr/bin/env python3

"""
Shell execution tools for Kimi Assistant

Handles bash and PowerShell command execution with security controls.
"""

from typing import Any, Dict

from .base import BaseTool, ToolResult
from ..utils.shell_utils import run_bash_command, run_powershell_command


class BashTool(BaseTool):
    """Handle run_bash function calls."""
    
    def get_name(self) -> str:
        return "run_bash"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute bash command with security confirmation."""
        try:
            command = args["command"]
            result = run_bash_command(command, self.config)
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.error(f"Error executing bash command: {str(e)}")


class PowerShellTool(BaseTool):
    """Handle run_powershell function calls."""
    
    def get_name(self) -> str:
        return "run_powershell"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute PowerShell command with security confirmation."""
        try:
            command = args["command"]
            result = run_powershell_command(command, self.config)
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.error(f"Error executing PowerShell command: {str(e)}")


def create_shell_tools(config) -> list[BaseTool]:
    """Create all shell tools."""
    return [
        BashTool(config),
        PowerShellTool(config)
    ]