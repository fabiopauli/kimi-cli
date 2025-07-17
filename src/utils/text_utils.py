#!/usr/bin/env python3

"""
Text processing utilities for Kimi Assistant

Handles token estimation, text truncation, and content analysis.
"""

from typing import List, Dict, Any, Tuple, Optional

from ..core.config import Config


def estimate_token_usage(conversation_history: List[Dict[str, Any]]) -> Tuple[int, Dict[str, int]]:
    """
    Estimate token usage for conversation history.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        Tuple of (total_tokens, breakdown_by_role)
    """
    # Try to use tiktoken if available
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        
        total_tokens = 0
        breakdown = {"system": 0, "user": 0, "assistant": 0, "tool": 0}
        
        for message in conversation_history:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            # Handle None content (can occur with tool calls)
            if content is None:
                content = ""
            
            # Count tokens
            tokens = len(encoding.encode(content))
            total_tokens += tokens
            
            if role in breakdown:
                breakdown[role] += tokens
            else:
                breakdown["user"] += tokens  # Default to user
        
        return total_tokens, breakdown
        
    except ImportError:
        # Fallback: rough estimation (1 token ≈ 4 characters)
        total_tokens = 0
        breakdown = {"system": 0, "user": 0, "assistant": 0, "tool": 0}
        
        for message in conversation_history:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            # Handle None content (can occur with tool calls)
            if content is None:
                content = ""
            
            # Rough estimation
            tokens = len(content) // 4
            total_tokens += tokens
            
            if role in breakdown:
                breakdown[role] += tokens
            else:
                breakdown["user"] += tokens  # Default to user
        
        return total_tokens, breakdown


def get_context_usage_info(conversation_history: List[Dict[str, Any]], 
                          model_name: str, config: Config) -> Dict[str, Any]:
    """
    Get detailed context usage information.
    
    Args:
        conversation_history: List of conversation messages
        model_name: Current model name
        config: Configuration object
        
    Returns:
        Dictionary with context usage information
    """
    estimated_tokens, breakdown = estimate_token_usage(conversation_history)
    max_tokens = config.get_max_tokens_for_model(model_name)
    
    usage_percent = (estimated_tokens / max_tokens) * 100
    
    return {
        "model": model_name,
        "messages": len(conversation_history),
        "estimated_tokens": estimated_tokens,
        "max_tokens": max_tokens,
        "token_usage_percent": usage_percent,
        "breakdown": breakdown,
        "approaching_limit": usage_percent >= (config.context_warning_threshold * 100),
        "critical_limit": usage_percent >= (config.aggressive_truncation_threshold * 100)
    }


def smart_truncate_history(conversation_history: List[Dict[str, Any]], 
                          model_name: str, config: Config) -> List[Dict[str, Any]]:
    """
    Smart truncation of conversation history using sliding window.
    
    Args:
        conversation_history: List of conversation messages
        model_name: Current model name
        config: Configuration object
        
    Returns:
        Truncated conversation history
    """
    if len(conversation_history) <= 1:
        return conversation_history
    
    # Always keep the first message (system prompt)
    system_prompt = conversation_history[0] if conversation_history else {}
    remaining_messages = conversation_history[1:]
    
    # Target token count (leave room for response)
    max_tokens = config.get_max_tokens_for_model(model_name)
    target_tokens = int(max_tokens * 0.6)  # Use 60% of context for history
    
    # Estimate tokens for system prompt
    system_tokens, _ = estimate_token_usage([system_prompt])
    available_tokens = target_tokens - system_tokens
    
    # Work backwards through messages to keep most recent
    selected_messages = []
    current_tokens = 0
    
    for message in reversed(remaining_messages):
        message_tokens, _ = estimate_token_usage([message])
        
        if current_tokens + message_tokens <= available_tokens:
            selected_messages.insert(0, message)
            current_tokens += message_tokens
        else:
            break
    
    # Ensure we have at least some conversation history
    if not selected_messages and remaining_messages:
        # If even the most recent message is too long, keep it anyway
        selected_messages = [remaining_messages[-1]]
    
    # Reconstruct with system prompt first
    result = [system_prompt] + selected_messages
    
    return result


def validate_tool_calls(accumulated_tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean tool calls.
    
    Args:
        accumulated_tool_calls: List of tool calls
        
    Returns:
        Validated and cleaned tool calls
    """
    valid_calls = []
    
    for call in accumulated_tool_calls:
        # Check required fields
        if not isinstance(call, dict):
            continue
        
        if "function" not in call:
            continue
        
        function = call["function"]
        if not isinstance(function, dict):
            continue
        
        if "name" not in function or "arguments" not in function:
            continue
        
        # Validate arguments is valid JSON
        try:
            import json
            json.loads(function["arguments"])
        except (json.JSONDecodeError, TypeError):
            continue
        
        valid_calls.append(call)
    
    return valid_calls


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_lines(text: str) -> int:
    """
    Count lines in text.
    
    Args:
        text: Text to count lines in
        
    Returns:
        Number of lines
    """
    return len(text.splitlines()) if text else 0


def extract_code_blocks(text: str, language: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown text.
    
    Args:
        text: Text to extract code blocks from
        language: Optional language filter
        
    Returns:
        List of code blocks with language and content
    """
    import re
    
    # Pattern to match code blocks
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for lang, content in matches:
        if language is None or lang == language:
            code_blocks.append({
                'language': lang or 'text',
                'content': content.strip()
            })
    
    return code_blocks


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def similarity_score(text1: str, text2: str) -> float:
    """
    Calculate similarity score between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        from thefuzz import fuzz
        return fuzz.ratio(text1, text2) / 100.0
    except ImportError:
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0