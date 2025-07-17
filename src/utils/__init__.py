"""
Utils module for Kimi Assistant

Contains utility functions organized by domain.
"""

from .path_utils import (
    normalize_path, get_directory_tree_summary, is_path_safe,
    get_relative_path, ensure_directory_exists, is_excluded_file
)

from .file_utils import (
    is_binary_file, detect_file_encoding, enhanced_binary_detection,
    safe_file_read, find_best_matching_file, apply_fuzzy_diff_edit,
    add_file_context_smartly
)

from .text_utils import (
    estimate_token_usage, get_context_usage_info, smart_truncate_history,
    validate_tool_calls, truncate_text, count_lines, extract_code_blocks,
    format_file_size, similarity_score
)

from .shell_utils import (
    detect_available_shells, run_bash_command, run_powershell_command,
    get_shell_for_os, is_dangerous_command, sanitize_command,
    validate_working_directory
)

__all__ = [
    # Path utilities
    'normalize_path', 'get_directory_tree_summary', 'is_path_safe',
    'get_relative_path', 'ensure_directory_exists', 'is_excluded_file',
    
    # File utilities
    'is_binary_file', 'detect_file_encoding', 'enhanced_binary_detection',
    'safe_file_read', 'find_best_matching_file', 'apply_fuzzy_diff_edit',
    'add_file_context_smartly',
    
    # Text utilities
    'estimate_token_usage', 'get_context_usage_info', 'smart_truncate_history',
    'validate_tool_calls', 'truncate_text', 'count_lines', 'extract_code_blocks',
    'format_file_size', 'similarity_score',
    
    # Shell utilities
    'detect_available_shells', 'run_bash_command', 'run_powershell_command',
    'get_shell_for_os', 'is_dangerous_command', 'sanitize_command',
    'validate_working_directory'
]