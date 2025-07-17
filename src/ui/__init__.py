"""
UI module for Kimi Assistant

Contains console interaction, formatting, and display logic.
"""

from .console import (
    get_console, get_prompt_session, initialize_prompt_session,
    get_prompt_indicator, display_startup_banner, display_context_warning,
    display_model_switch, display_file_added, display_directory_tree,
    display_error, display_success, display_info, display_warning,
    clear_screen, display_thinking_indicator, display_tool_call,
    display_security_confirmation
)

from .formatters import (
    format_conversation_log, format_file_content, format_directory_tree,
    format_context_stats, format_tool_result, format_error_message,
    format_success_message, format_info_message, format_warning_message
)

__all__ = [
    # Console functions
    'get_console', 'get_prompt_session', 'initialize_prompt_session',
    'get_prompt_indicator', 'display_startup_banner', 'display_context_warning',
    'display_model_switch', 'display_file_added', 'display_directory_tree',
    'display_error', 'display_success', 'display_info', 'display_warning',
    'clear_screen', 'display_thinking_indicator', 'display_tool_call',
    'display_security_confirmation',
    
    # Formatter functions
    'format_conversation_log', 'format_file_content', 'format_directory_tree',
    'format_context_stats', 'format_tool_result', 'format_error_message',
    'format_success_message', 'format_info_message', 'format_warning_message'
]