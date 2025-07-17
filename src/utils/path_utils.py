#!/usr/bin/env python3

"""
Path utilities for Kimi Assistant

Handles path normalization, validation, and directory operations.
"""

import os
from pathlib import Path
from typing import Optional, Union

from ..core.config import Config


def normalize_path(path_str: str, config: Config, allow_outside_project: bool = False) -> str:
    """
    Normalize and validate a file path relative to the base directory.
    
    This function provides security by preventing directory traversal attacks
    and ensures all paths are relative to the project base directory.
    
    Args:
        path_str: The path string to normalize
        config: Configuration object
        allow_outside_project: Whether to allow paths outside the project
        
    Returns:
        Normalized absolute path as string
        
    Raises:
        ValueError: If path is outside base directory and not allowed
        FileNotFoundError: If path doesn't exist when validation is needed
    """
    # Handle empty or None paths
    if not path_str or not path_str.strip():
        raise ValueError("Path cannot be empty")
    
    path_str = path_str.strip()
    
    # Convert to Path object
    if os.path.isabs(path_str):
        # Absolute path
        normalized_path = Path(path_str).resolve()
    else:
        # Relative path - make it relative to base_dir
        normalized_path = (config.base_dir / path_str).resolve()
    
    # Security check: ensure path is within base directory
    if not allow_outside_project:
        try:
            # This will raise ValueError if path is outside base_dir
            normalized_path.relative_to(config.base_dir)
        except ValueError:
            raise ValueError(
                f"Security: Path '{path_str}' resolves to '{normalized_path}' "
                f"which is outside the base directory '{config.base_dir}'. "
                f"This is not allowed for security reasons."
            )
    
    return str(normalized_path)


def get_directory_tree_summary(root_dir: Path, config: Config, max_depth: int = 3, max_entries: int = 100) -> str:
    """
    Generate a concise summary of the directory structure.
    
    Args:
        root_dir: Root directory to scan
        config: Configuration object
        max_depth: Maximum depth to traverse
        max_entries: Maximum number of entries to include
        
    Returns:
        Formatted directory tree summary
    """
    if not root_dir.exists() or not root_dir.is_dir():
        return f"Directory '{root_dir}' does not exist or is not a directory."
    
    entries = []
    entry_count = 0
    
    def scan_directory(path: Path, depth: int = 0, prefix: str = "") -> None:
        nonlocal entry_count
        
        if depth > max_depth or entry_count >= max_entries:
            return
        
        try:
            # Get directory contents, sorted
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for i, item in enumerate(items):
                if entry_count >= max_entries:
                    break
                
                # Skip excluded files and directories
                if item.name in config.excluded_files:
                    continue
                
                if item.suffix.lower() in config.excluded_extensions:
                    continue
                
                # Determine if this is the last item
                is_last = i == len(items) - 1
                
                # Create tree structure
                if depth == 0:
                    current_prefix = ""
                    next_prefix = ""
                else:
                    current_prefix = prefix + ("└── " if is_last else "├── ")
                    next_prefix = prefix + ("    " if is_last else "│   ")
                
                if item.is_dir():
                    entries.append(f"{current_prefix}📁 {item.name}/")
                    entry_count += 1
                    
                    # Recursively scan subdirectory
                    if depth < max_depth:
                        scan_directory(item, depth + 1, next_prefix)
                else:
                    # File
                    entries.append(f"{current_prefix}📄 {item.name}")
                    entry_count += 1
        
        except PermissionError:
            entries.append(f"{prefix}❌ Permission denied")
            entry_count += 1
        except Exception as e:
            entries.append(f"{prefix}❌ Error: {str(e)}")
            entry_count += 1
    
    # Start scanning
    entries.append(f"📁 {root_dir.name}/")
    entry_count += 1
    scan_directory(root_dir)
    
    # Add truncation notice if needed
    if entry_count >= max_entries:
        entries.append("...")
        entries.append(f"(Truncated at {max_entries} entries)")
    
    return "\n".join(entries)


def is_path_safe(path: Union[str, Path], config: Config) -> bool:
    """
    Check if a path is safe to access.
    
    Args:
        path: Path to check
        config: Configuration object
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        normalized = normalize_path(str(path), config, allow_outside_project=False)
        return True
    except (ValueError, OSError):
        return False


def get_relative_path(path: Union[str, Path], base_dir: Path) -> str:
    """
    Get relative path from base directory.
    
    Args:
        path: Path to make relative
        base_dir: Base directory
        
    Returns:
        Relative path string
    """
    try:
        path_obj = Path(path).resolve()
        return str(path_obj.relative_to(base_dir))
    except ValueError:
        # Path is outside base_dir, return absolute path
        return str(Path(path).resolve())


def ensure_directory_exists(path: Union[str, Path]) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def is_excluded_file(file_path: Union[str, Path], config: Config) -> bool:
    """
    Check if a file should be excluded based on configuration.
    
    Args:
        file_path: File path to check
        config: Configuration object
        
    Returns:
        True if file should be excluded, False otherwise
    """
    path = Path(file_path)
    
    # Check excluded files
    if path.name in config.excluded_files:
        return True
    
    # Check excluded extensions
    if path.suffix.lower() in config.excluded_extensions:
        return True
    
    return False