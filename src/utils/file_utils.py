#!/usr/bin/env python3

"""
File utilities for Kimi Assistant

Handles file reading, writing, encoding detection, and fuzzy matching.
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union

from ..core.config import Config
from .path_utils import normalize_path


def is_binary_file(file_path: str, peek_size: int = 8192) -> bool:
    """
    Check if a file is binary using multiple heuristics.
    
    Args:
        file_path: Path to the file
        peek_size: Number of bytes to peek at
        
    Returns:
        True if file appears to be binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(peek_size)
            
        # Empty file is considered text
        if not chunk:
            return False
            
        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return True
            
        # Check for high percentage of non-printable characters
        printable_chars = 0
        for byte in chunk:
            if 32 <= byte <= 126 or byte in (9, 10, 13):  # ASCII printable + tab/newline/carriage return
                printable_chars += 1
        
        # If less than 70% printable characters, consider it binary
        if printable_chars / len(chunk) < 0.70:
            return True
            
        return False
        
    except (IOError, OSError):
        return True  # Assume binary if can't read


def detect_file_encoding(file_path: str, peek_size: int = 8192) -> Tuple[str, float]:
    """
    Detect file encoding using chardet library or fallback methods.
    
    Args:
        file_path: Path to the file
        peek_size: Number of bytes to peek at
        
    Returns:
        Tuple of (encoding, confidence)
    """
    try:
        # Try to import chardet for better encoding detection
        import chardet
        
        with open(file_path, 'rb') as f:
            raw_data = f.read(peek_size)
            
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8', result['confidence'] or 0.0
        
    except ImportError:
        # Fallback method without chardet
        encodings_to_try = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(peek_size)
                return encoding, 0.8  # Reasonable confidence for successful decode
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'utf-8', 0.1  # Low confidence fallback


def enhanced_binary_detection(file_path: str, peek_size: int = 8192) -> Dict[str, Any]:
    """
    Enhanced binary file detection with detailed analysis.
    
    Args:
        file_path: Path to the file
        peek_size: Number of bytes to peek at
        
    Returns:
        Dictionary with detection results
    """
    result = {
        'is_binary': False,
        'file_type': 'text',
        'mime_type': 'text/plain',
        'confidence': 0.0,
        'analysis': {}
    }
    
    try:
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            result['mime_type'] = mime_type
            
            # Common binary MIME types
            if mime_type.startswith(('image/', 'video/', 'audio/', 'application/octet-stream')):
                result['is_binary'] = True
                result['file_type'] = mime_type.split('/')[0]
                result['confidence'] = 0.9
                return result
        
        # Read file content for analysis
        with open(file_path, 'rb') as f:
            chunk = f.read(peek_size)
        
        if not chunk:
            result['file_type'] = 'empty'
            return result
        
        # Analyze content
        null_bytes = chunk.count(b'\x00')
        total_bytes = len(chunk)
        
        # Count printable characters
        printable = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
        printable_ratio = printable / total_bytes if total_bytes > 0 else 0
        
        result['analysis'] = {
            'total_bytes': total_bytes,
            'null_bytes': null_bytes,
            'printable_chars': printable,
            'printable_ratio': printable_ratio,
            'null_ratio': null_bytes / total_bytes if total_bytes > 0 else 0
        }
        
        # Decision logic
        if null_bytes > 0:
            result['is_binary'] = True
            result['file_type'] = 'binary'
            result['confidence'] = 0.95
        elif printable_ratio < 0.70:
            result['is_binary'] = True
            result['file_type'] = 'binary'
            result['confidence'] = 0.85
        else:
            result['is_binary'] = False
            result['file_type'] = 'text'
            result['confidence'] = 0.8
        
        return result
        
    except (IOError, OSError) as e:
        result['is_binary'] = True
        result['file_type'] = 'error'
        result['analysis']['error'] = str(e)
        return result


def safe_file_read(file_path: str, max_size: Optional[int] = None, config: Config = None) -> Dict[str, Any]:
    """
    Safely read a file with comprehensive error handling and size limits.
    
    Args:
        file_path: Path to the file
        max_size: Maximum file size in bytes
        config: Configuration object
        
    Returns:
        Dictionary with read results
    """
    result = {
        'success': False,
        'content': '',
        'error': '',
        'warnings': [],
        'file_info': {},
        'encoding_info': {}
    }
    
    try:
        # Normalize path
        if config:
            normalized_path = normalize_path(file_path, config)
        else:
            normalized_path = str(Path(file_path).resolve())
        
        # Check if file exists
        if not os.path.exists(normalized_path):
            result['error'] = f"File not found: {normalized_path}"
            result['file_info']['error_type'] = 'FileNotFound'
            return result
        
        # Check if it's a file
        if not os.path.isfile(normalized_path):
            result['error'] = f"Path is not a file: {normalized_path}"
            result['file_info']['error_type'] = 'NotAFile'
            return result
        
        # Get file info
        file_stat = os.stat(normalized_path)
        file_size = file_stat.st_size
        
        result['file_info'] = {
            'size_bytes': file_size,
            'size_kb': file_size / 1024,
            'size_mb': file_size / (1024 * 1024),
            'modified_time': file_stat.st_mtime,
            'path': normalized_path
        }
        
        # Check size limit
        if max_size and file_size > max_size:
            result['error'] = f"File exceeds size limit: {file_size} bytes > {max_size} bytes"
            result['file_info']['error_type'] = 'FileTooLarge'
            return result
        
        # Enhanced binary detection
        detection_result = enhanced_binary_detection(normalized_path)
        result['file_info']['detection'] = detection_result
        
        if detection_result['is_binary']:
            result['error'] = f"File appears to be binary: {detection_result['file_type']}"
            result['file_info']['error_type'] = 'BinaryFile'
            return result
        
        # Detect encoding
        encoding, confidence = detect_file_encoding(normalized_path)
        result['encoding_info'] = {
            'detected_encoding': encoding,
            'confidence': confidence
        }
        
        # Add warning for low confidence encoding
        if confidence < 0.8:
            result['warnings'].append(f"Low confidence encoding detection: {encoding} ({confidence:.1%})")
        
        # Read file content
        with open(normalized_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        result['success'] = True
        result['content'] = content
        
        # Add warnings for replaced characters
        if '�' in content:
            result['warnings'].append("Some characters were replaced due to encoding issues")
        
        return result
        
    except PermissionError:
        result['error'] = f"Permission denied: {file_path}"
        result['file_info']['error_type'] = 'PermissionDenied'
        return result
    except UnicodeDecodeError as e:
        result['error'] = f"Encoding error: {str(e)}"
        result['file_info']['error_type'] = 'EncodingError'
        return result
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        result['file_info']['error_type'] = 'UnknownError'
        return result


def find_best_matching_file(root_dir: Path, user_path: str, config: Config, min_score: int = None) -> Optional[str]:
    """
    Find the best matching file using fuzzy matching.
    
    Args:
        root_dir: Root directory to search
        user_path: User-provided path to match
        config: Configuration object
        min_score: Minimum matching score (uses config default if None)
        
    Returns:
        Best matching file path or None
    """
    if not config.fuzzy_available:
        return None
    
    if min_score is None:
        min_score = config.min_fuzzy_score
    
    try:
        from thefuzz import fuzz, process as fuzzy_process
        
        # Collect all files
        all_files = []
        for root, dirs, files in os.walk(root_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in config.excluded_files]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip excluded files
                if file in config.excluded_files:
                    continue
                
                # Skip excluded extensions
                if file_path.suffix.lower() in config.excluded_extensions:
                    continue
                
                # Store relative path
                try:
                    relative_path = file_path.relative_to(root_dir)
                    all_files.append(str(relative_path))
                except ValueError:
                    continue
        
        if not all_files:
            return None
        
        # Find best match
        best_match, score = fuzzy_process.extractOne(user_path, all_files, scorer=fuzz.ratio)
        
        if score >= min_score:
            return str(root_dir / best_match)
        
        return None
        
    except ImportError:
        return None
    except Exception:
        return None


def apply_fuzzy_diff_edit(path: str, original_snippet: str, new_snippet: str, config: Config) -> None:
    """
    Apply fuzzy diff edit to a file.
    
    Args:
        path: Path to the file
        original_snippet: Original snippet to replace
        new_snippet: New snippet to replace with
        config: Configuration object
    """
    # Import here to avoid circular imports
    from ..ui.console import get_console
    
    console = get_console()
    
    # Normalize path
    normalized_path = normalize_path(path, config)
    
    # Read file
    with open(normalized_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Try exact match first
    if original_snippet in content:
        new_content = content.replace(original_snippet, new_snippet)
        
        with open(normalized_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        console.print(f"[bold blue]✓[/bold blue] Applied exact edit to '[bright_cyan]{normalized_path}[/bright_cyan]'")
        return
    
    # 2. If exact match fails, use fuzzy matching (if available and enabled)
    if not config.fuzzy_available or not config.fuzzy_enabled_by_default:
        raise ValueError("Original snippet not found and fuzzy matching not available or disabled")
    
    from thefuzz import fuzz, process as fuzzy_process
    
    console.print("[dim]Exact snippet not found. Trying fuzzy matching...[/dim]")
    
    # Split content into lines for fuzzy matching
    lines = content.split('\n')
    snippet_lines = original_snippet.split('\n')
    
    # Create sliding window of lines to match against
    window_size = len(snippet_lines)
    if window_size > len(lines):
        raise ValueError("Original snippet is longer than the file content.")
    
    # Find best matching window
    best_match = None
    best_score = 0
    best_start = 0
    
    for i in range(len(lines) - window_size + 1):
        window = '\n'.join(lines[i:i + window_size])
        score = fuzz.ratio(original_snippet, window)
        
        if score > best_score:
            best_score = score
            best_match = window
            best_start = i
    
    # Check if match is good enough
    if best_score < config.min_edit_score:
        raise ValueError(f"No good fuzzy match found. Best score: {best_score}")
    
    # Check for ambiguous matches
    matches_above_threshold = 0
    for i in range(len(lines) - window_size + 1):
        window = '\n'.join(lines[i:i + window_size])
        if fuzz.ratio(original_snippet, window) >= config.min_edit_score:
            matches_above_threshold += 1
    
    if matches_above_threshold > 1:
        raise ValueError(f"Ambiguous fuzzy edit: The best matching snippet appears multiple times in the file.")
    
    # Replace the best fuzzy match
    new_lines = lines[:best_start] + new_snippet.split('\n') + lines[best_start + window_size:]
    new_content = '\n'.join(new_lines)
    
    with open(normalized_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    console.print(f"[bold blue]✓[/bold blue] Applied [bold]fuzzy[/bold] diff edit to '[bright_cyan]{normalized_path}[/bright_cyan]' (score: {best_score})")


def add_file_context_smartly(file_path: str, session, config: Config) -> None:
    """
    Add file context to session with smart handling.
    
    Args:
        file_path: Path to the file
        session: Session object
        config: Configuration object
    """
    # Import here to avoid circular imports
    from ..ui.console import get_console
    
    console = get_console()
    
    # Normalize path
    normalized_path = normalize_path(file_path, config)
    path_obj = Path(normalized_path)
    
    if path_obj.is_file():
        # Single file
        read_result = safe_file_read(normalized_path, config=config)
        
        if read_result['success']:
            relative_path = path_obj.relative_to(config.base_dir)
            session.add_message("system", f"User added file '{relative_path}':\n\n{read_result['content']}")
            console.print(f"[bold green]✓[/bold green] Added file to context: '[bright_cyan]{relative_path}[/bright_cyan]'")
        else:
            console.print(f"[bold red]✗[/bold red] Failed to read file: {read_result['error']}")
            raise Exception(read_result['error'])
    
    elif path_obj.is_dir():
        # Directory
        files_added = 0
        total_size = 0
        
        # Walk through directory
        for root, dirs, files in os.walk(path_obj):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in config.excluded_files]
            
            for file in files:
                file_path_obj = Path(root) / file
                
                # Skip excluded files
                if file in config.excluded_files:
                    continue
                
                # Skip excluded extensions
                if file_path_obj.suffix.lower() in config.excluded_extensions:
                    continue
                
                # Check size limits
                if total_size > config.max_multiple_read_size:
                    break
                
                if files_added >= config.max_files_in_add_dir:
                    break
                
                # Read file
                read_result = safe_file_read(str(file_path_obj), config=config)
                
                if read_result['success']:
                    relative_path = file_path_obj.relative_to(config.base_dir)
                    session.add_message("system", f"User added file '{relative_path}':\n\n{read_result['content']}")
                    files_added += 1
                    total_size += len(read_result['content'])
            
            if files_added >= config.max_files_in_add_dir or total_size > config.max_multiple_read_size:
                break
        
        relative_dir = path_obj.relative_to(config.base_dir)
        console.print(f"[bold green]✓[/bold green] Added {files_added} files from directory '[bright_cyan]{relative_dir}[/bright_cyan]' to context")
    
    else:
        raise Exception(f"Path is neither file nor directory: {normalized_path}")