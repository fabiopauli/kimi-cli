#!/usr/bin/env python3

"""
Main application for Kimi Assistant (Refactored)

This is the new, thin orchestrator that coordinates all the modular components.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Import our refactored modules
from src.core.config import Config
from src.core.session import KimiSession
from src.commands import create_command_registry
from src.tools import create_tool_executor
from src.ui import (
    get_console, get_prompt_session, initialize_prompt_session,
    get_prompt_indicator, display_startup_banner, display_thinking_indicator,
    display_tool_call, display_error
)
from src.utils.shell_utils import detect_available_shells


def initialize_application() -> tuple[Config, Groq, object, object]:
    """
    Initialize the application with all required components.
    
    Returns:
        Tuple of (config, client, command_registry, tool_executor)
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize configuration
    config = Config()
    
    # Detect available shells
    detect_available_shells(config)
    
    # Initialize Groq client
    client = Groq()
    
    # Initialize UI components
    initialize_prompt_session()
    
    # Create command registry
    command_registry = create_command_registry(config)
    
    # Create tool executor
    tool_executor = create_tool_executor(config)
    
    return config, client, command_registry, tool_executor


def handle_tool_calls(response, tool_executor, session):
    """
    Handle tool calls from the AI response.
    
    Args:
        response: Response from AI
        tool_executor: Tool executor instance
        session: Current session
        
    Returns:
        List of tool results
    """
    console = get_console()
    tool_results = []
    
    # Debug: Show what we're working with
    console.print(f"[dim]Response has tool_calls: {hasattr(response, 'tool_calls') and response.tool_calls}[/dim]")
    console.print(f"[dim]Response has content: {hasattr(response, 'content') and response.content}[/dim]")
    if hasattr(response, 'content') and response.content:
        console.print(f"[dim]Content preview: {response.content[:200]}...[/dim]")
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            display_tool_call(tool_call.function.name, {})
            
            # Execute tool call
            result = tool_executor.execute_tool_call({
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            })
            
            # Add tool result to session with proper tool_call_id
            session.add_message("tool", result, tool_call_id=tool_call.id)
            tool_results.append(result)
    elif hasattr(response, 'content') and response.content:
        # Fallback: Parse text-based tool calls for models that don't support proper tool calls
        console.print("[dim]Trying text-based tool call parsing...[/dim]")
        tool_results.extend(parse_text_tool_calls(response.content, tool_executor, session))
    
    return tool_results


def parse_text_tool_calls(content, tool_executor, session):
    """
    Parse tool calls from text content for models that output them as text.
    
    Args:
        content: Response content that may contain text-based tool calls
        tool_executor: Tool executor instance
        session: Current session
        
    Returns:
        List of tool results
    """
    import re
    import json
    
    console = get_console()
    tool_results = []
    
    # Pattern to match <function=name{...}</function> format
    pattern = r'<function=([^{]+)\{(.*?)\}</function>'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if matches:
        console.print(f"[dim]Found {len(matches)} text-based tool calls[/dim]")
    else:
        console.print(f"[dim]No text-based tool calls found in: {content[:100]}...[/dim]")
    
    for function_name, arguments_str in matches:
        try:
            # Parse the arguments JSON
            arguments = json.loads('{' + arguments_str + '}')
            
            display_tool_call(function_name, arguments)
            
            # Execute tool call
            result = tool_executor.execute_tool_call({
                "function": {
                    "name": function_name,
                    "arguments": arguments
                }
            })
            
            # Add tool result to session (no tool_call_id for text-based calls)
            session.add_message("tool", result)
            tool_results.append(result)
            
        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[red]Error parsing tool call: {e}[/red]")
            console.print(f"[dim]Function: {function_name}, Arguments: {arguments_str}[/dim]")
    
    return tool_results


def main_loop(config: Config, client: Groq, command_registry, tool_executor) -> None:
    """
    Main application loop.
    
    Args:
        config: Configuration object
        client: Groq client
        command_registry: Command registry
        tool_executor: Tool executor
    """
    console = get_console()
    prompt_session = get_prompt_session()
    
    # Initialize session
    session = KimiSession(client, config)
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            conversation_history = session.get_conversation_history()
            prompt_indicator = get_prompt_indicator(conversation_history, session.model)
            user_input = prompt_session.prompt(f"{prompt_indicator} ")
            
            if not user_input.strip():
                continue
            
            # Try to handle as command first
            command_result = command_registry.execute_command(user_input, session)
            if command_result:
                # Command was executed
                if not command_result.should_continue:
                    break
                continue
            
            # Add user message to session
            session.add_message("user", user_input)
            
            # Show thinking indicator
            display_thinking_indicator()
            
            # Get AI response (check if one-time reasoner is requested)
            response = session.get_response()
            
            # Multi-step reasoning loop: Continue until no more tool calls
            step_count = 0
            max_steps = config.max_reasoning_steps
            
            # Check for both proper tool calls and text-based tool calls
            has_tool_calls = (hasattr(response, 'tool_calls') and response.tool_calls) or \
                           (hasattr(response, 'content') and response.content and 
                            '<function=' in response.content)
            
            while has_tool_calls and step_count < max_steps:
                step_count += 1
                
                # Handle the current batch of tool calls
                tool_results = handle_tool_calls(response, tool_executor, session)
                
                # Display assistant response if it has content
                if hasattr(response, 'content') and response.content:
                    console.print(f"\nKimi CLI - assistant msg: {response.content}\n")
                
                # Get the next response from the model to analyze tool results
                if step_count < max_steps:
                    console.print(f"[dim]Step {step_count}: Analyzing tool results...[/dim]")
                    display_thinking_indicator()
                    response = session.get_response()
                    
                    # Check for more tool calls in the new response
                    has_tool_calls = (hasattr(response, 'tool_calls') and response.tool_calls) or \
                                   (hasattr(response, 'content') and response.content and 
                                    '<function=' in response.content)
                else:
                    console.print(f"[yellow]Maximum reasoning steps ({max_steps}) reached.[/yellow]")
                    break
            
            # Display completion summary if multi-step reasoning occurred
            if step_count > 0:
                console.print(f"[dim]Completed reasoning in {step_count} step{'s' if step_count != 1 else ''}.[/dim]")
            
            # Display final response (without tool calls)
            if hasattr(response, 'content') and response.content:
                console.print(f"\nKimi CLI - assistant msg: {response.content}\n")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user.[/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]EOF received, exiting.[/yellow]")
            break
        except Exception as e:
            display_error(f"Unexpected error: {str(e)}")
            console.print("[dim]Please try again or use /help for assistance.[/dim]")


def main() -> None:
    """Main entry point."""
    console = get_console()
    
    try:
        # Initialize application
        config, client, command_registry, tool_executor = initialize_application()
        
        # Display startup banner
        display_startup_banner()
        
        # Start main loop
        main_loop(config, client, command_registry, tool_executor)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Application interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        display_error(f"Failed to initialize application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()