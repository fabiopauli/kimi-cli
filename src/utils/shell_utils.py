#!/usr/bin/env python3

"""
Shell utilities for Kimi Assistant

Handles shell command execution with security controls.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Union, Tuple

from ..core.config import Config


def detect_available_shells(config: Config) -> None:
    """
    Detect which shells are available on the system.
    
    Args:
        config: Configuration object to update
    """
    shells = ['bash', 'zsh', 'powershell', 'cmd']
    
    for shell in shells:
        if shell == 'cmd' and config.os_info['is_windows']:
            # cmd is always available on Windows
            config.os_info['shell_available'][shell] = True
        elif shell == 'powershell':
            # Check for both Windows PowerShell and PowerShell Core
            config.os_info['shell_available'][shell] = (
                shutil.which('powershell') is not None or 
                shutil.which('pwsh') is not None
            )
        else:
            config.os_info['shell_available'][shell] = shutil.which(shell) is not None


def run_bash_command(command: str, config: Config, 
                    cwd: Optional[Union[str, Path]] = None) -> str:
    """
    Execute a bash command with security confirmation.
    
    Args:
        command: Command to execute
        config: Configuration object
        cwd: Working directory
        
    Returns:
        Command output
    """
    # Import here to avoid circular imports
    from ..ui.console import display_security_confirmation
    
    # Security confirmation
    if config.require_bash_confirmation:
        if not display_security_confirmation(command, "bash"):
            return "Command execution cancelled by user."
    
    # Set working directory
    if cwd is None:
        cwd = config.base_dir
    
    try:
        # Use bash explicitly to ensure consistent behavior
        result = subprocess.run(
            ['bash', '-c', command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # Format output
        output_parts = []
        
        if result.stdout:
            output_parts.append(f"stdout:\n{result.stdout}")
        
        if result.stderr:
            output_parts.append(f"stderr:\n{result.stderr}")
        
        if result.returncode != 0:
            output_parts.append(f"Exit code: {result.returncode}")
        
        return "\n".join(output_parts) if output_parts else "Command completed with no output."
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 30 seconds: {command}"
    except FileNotFoundError:
        return "Error: bash not found. Please ensure bash is installed and in your PATH."
    except Exception as e:
        return f"Error executing bash command: {str(e)}"


def run_powershell_command(command: str, config: Config, 
                          cwd: Optional[Union[str, Path]] = None) -> str:
    """
    Execute a PowerShell command with security confirmation.
    
    Args:
        command: Command to execute
        config: Configuration object
        cwd: Working directory
        
    Returns:
        Command output
    """
    # Import here to avoid circular imports
    from ..ui.console import display_security_confirmation
    
    # Security confirmation
    if config.require_powershell_confirmation:
        if not display_security_confirmation(command, "powershell"):
            return "Command execution cancelled by user."
    
    # Set working directory
    if cwd is None:
        cwd = config.base_dir
    
    try:
        # Try PowerShell Core first (pwsh), then Windows PowerShell
        powershell_exe = 'pwsh' if shutil.which('pwsh') else 'powershell'
        
        # Use -Command parameter for better compatibility
        result = subprocess.run(
            [powershell_exe, '-Command', command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # Format output
        output_parts = []
        
        if result.stdout:
            output_parts.append(f"stdout:\n{result.stdout}")
        
        if result.stderr:
            output_parts.append(f"stderr:\n{result.stderr}")
        
        if result.returncode != 0:
            output_parts.append(f"Exit code: {result.returncode}")
        
        return "\n".join(output_parts) if output_parts else "Command completed with no output."
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 30 seconds: {command}"
    except FileNotFoundError:
        return f"Error: {powershell_exe} not found. Please ensure PowerShell is installed and in your PATH."
    except Exception as e:
        return f"Error executing PowerShell command: {str(e)}"


def get_shell_for_os(config: Config) -> str:
    """
    Get the appropriate shell for the current OS.
    
    Args:
        config: Configuration object
        
    Returns:
        Shell name
    """
    if config.os_info['is_windows']:
        if config.os_info['shell_available']['powershell']:
            return 'powershell'
        elif config.os_info['shell_available']['cmd']:
            return 'cmd'
    else:
        if config.os_info['shell_available']['bash']:
            return 'bash'
        elif config.os_info['shell_available']['zsh']:
            return 'zsh'
    
    return 'unknown'


def is_dangerous_command(command: str) -> bool:
    """
    Check if a command is potentially dangerous.
    
    Args:
        command: Command to check
        
    Returns:
        True if command is dangerous, False otherwise
    """
    dangerous_patterns = [
        'rm -rf /',
        'del /f /s /q',
        'format',
        'fdisk',
        'dd if=',
        'shutdown',
        'reboot',
        'halt',
        'poweroff',
        'mkfs',
        'wipefs',
        'shred',
        'chown -R',
        'chmod -R 777',
        'sudo su',
        'su root',
        '> /dev/null',
        'curl | bash',
        'wget | bash',
        'eval $(',
        'exec(',
        '$(curl',
        '$(wget',
    ]
    
    command_lower = command.lower()
    
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return True
    
    return False


def sanitize_command(command: str) -> str:
    """
    Sanitize a command by removing dangerous elements.
    
    Args:
        command: Command to sanitize
        
    Returns:
        Sanitized command
    """
    # Remove null bytes
    command = command.replace('\x00', '')
    
    # Remove control characters
    command = ''.join(char for char in command if ord(char) >= 32 or char in '\t\n\r')
    
    # Limit length
    if len(command) > 1000:
        command = command[:1000]
    
    return command.strip()


def validate_working_directory(cwd: Union[str, Path], config: Config) -> bool:
    """
    Validate that a working directory is safe to use.
    
    Args:
        cwd: Working directory path
        config: Configuration object
        
    Returns:
        True if directory is safe, False otherwise
    """
    try:
        cwd_path = Path(cwd).resolve()
        
        # Check if directory exists
        if not cwd_path.exists() or not cwd_path.is_dir():
            return False
        
        # Check if directory is within base directory
        try:
            cwd_path.relative_to(config.base_dir)
            return True
        except ValueError:
            # Directory is outside base directory
            return False
    
    except (OSError, ValueError):
        return False