#!/usr/bin/env python3

"""
File operation tools for Kimi Assistant

Handles file reading, writing, and editing operations.
"""

import json
from pathlib import Path
from typing import Any, Dict

from .base import BaseTool, ToolResult
from ..utils.path_utils import normalize_path
from ..utils.file_utils import safe_file_read, apply_fuzzy_diff_edit


class ReadFileTool(BaseTool):
    """Handle read_file function calls."""
    
    def get_name(self) -> str:
        return "read_file"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute read_file with enhanced error handling."""
        try:
            norm_path = normalize_path(args["file_path"], self.config)
            
            # Get model-specific context limit
            current_model = self.config.current_model
            max_tokens = self.config.get_max_tokens_for_model(current_model)
            max_file_tokens = int(max_tokens * 0.6)
            max_file_size = max_file_tokens * 4  # Convert tokens to approximate bytes
            
            # Use safe_file_read for comprehensive handling
            read_result = safe_file_read(norm_path, max_size=max_file_size, config=self.config)
            
            if not read_result['success']:
                error_msg = read_result['error']
                error_type = read_result['file_info'].get('error_type', 'Unknown')
                
                # Provide helpful error messages based on error type
                if 'binary' in error_msg.lower():
                    file_type = read_result['file_info'].get('detection', {}).get('file_type', 'unknown')
                    return ToolResult.error(f"Error: Cannot read binary file '{norm_path}' as text.\nFile type: {file_type}\nSuggestion: This appears to be a binary file. If you need to examine it, consider using a hex editor or file-specific tools.")
                    
                elif 'exceeds limit' in error_msg:
                    file_size_kb = read_result['file_info'].get('size_kb', 0)
                    return ToolResult.error(f"Error: File '{norm_path}' is too large ({file_size_kb:.1f}KB) to read safely.\nCurrent limit: {max_file_size/1024:.1f}KB for model {current_model}\nSuggestion: Try reading specific sections of the file or use a streaming approach for large files.")
                    
                elif 'permission denied' in error_msg.lower():
                    return ToolResult.error(f"Error: Permission denied accessing '{norm_path}'.\nSuggestion: Check file permissions or run with appropriate access rights.")
                    
                elif 'not found' in error_msg.lower():
                    return ToolResult.error(f"Error: File not found: '{norm_path}'.\nSuggestion: Check the file path and ensure the file exists.")
                    
                elif 'locked' in error_msg.lower():
                    return ToolResult.error(f"Error: File '{norm_path}' is currently in use by another process.\nSuggestion: Close any applications that might be using this file and try again.")
                    
                else:
                    return ToolResult.error(f"Error reading file '{norm_path}': {error_msg}\nError type: {error_type}")
            
            # Add warnings to output if any
            warnings_text = ""
            if read_result['warnings']:
                warnings_text = f"\nWarnings: {'; '.join(read_result['warnings'])}"
            
            # Add encoding information if confidence is low
            encoding_info = ""
            encoding_data = read_result['encoding_info']
            if encoding_data.get('confidence', 1.0) < 0.8:
                encoding_info = f"\nNote: File encoding detected as {encoding_data['detected_encoding']} with {encoding_data['confidence']:.1%} confidence."
            
            return ToolResult.success(f"Content of file '{norm_path}':{warnings_text}{encoding_info}\n\n{read_result['content']}")
            
        except Exception as e:
            return ToolResult.error(f"Unexpected error reading file '{args.get('file_path', 'unknown')}': {str(e)}\nSuggestion: Check the file path and try again.")


class ReadMultipleFilesTool(BaseTool):
    """Handle read_multiple_files function calls."""
    
    def get_name(self) -> str:
        return "read_multiple_files"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute read_multiple_files with size limits."""
        response_data = {
            "files_read": {},
            "errors": {},
            "warnings": {},
            "metadata": {}
        }
        total_content_size = 0
        
        # Get model-specific context limit for multiple files
        current_model = self.config.current_model
        max_tokens = self.config.get_max_tokens_for_model(current_model)
        # Use smaller percentage for multiple files to be safer
        max_total_tokens = int(max_tokens * 0.4)
        max_total_size = max_total_tokens * 4  # Convert tokens back to character estimate
        max_single_file_size = max_total_size // 2  # Individual file limit

        response_data["metadata"]["limits"] = {
            "max_total_size_kb": max_total_size / 1024,
            "max_single_file_size_kb": max_single_file_size / 1024,
            "model": current_model
        }

        for fp in args["file_paths"]:
            try:
                norm_path = normalize_path(fp, self.config)
                
                # Use safe_file_read for comprehensive handling
                read_result = safe_file_read(norm_path, max_size=max_single_file_size, config=self.config)
                
                if not read_result['success']:
                    response_data["errors"][fp] = read_result['error']
                    continue
                
                # Check total size limit
                content_size = len(read_result['content'])
                if total_content_size + content_size > max_total_size:
                    response_data["errors"][fp] = f"Would exceed total size limit ({max_total_size/1024:.1f}KB)"
                    continue
                
                total_content_size += content_size
                response_data["files_read"][fp] = read_result['content']
                
                # Collect warnings
                if read_result['warnings']:
                    response_data["warnings"][fp] = read_result['warnings']
                
            except Exception as e:
                response_data["errors"][fp] = f"Unexpected error: {str(e)}"
        
        response_data["metadata"]["total_size_kb"] = total_content_size / 1024
        response_data["metadata"]["files_processed"] = len(args["file_paths"])
        response_data["metadata"]["files_read"] = len(response_data["files_read"])
        response_data["metadata"]["files_error"] = len(response_data["errors"])
        
        return ToolResult.success(json.dumps(response_data, indent=2))


class CreateFileTool(BaseTool):
    """Handle create_file function calls."""
    
    def get_name(self) -> str:
        return "create_file"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute create_file with validation."""
        try:
            norm_path = normalize_path(args["file_path"], self.config)
            content = args["content"]
            
            # Validate content size
            if len(content) > self.config.max_file_content_size_create:
                return ToolResult.error(f"Error: Content too large ({len(content)} chars). Maximum allowed: {self.config.max_file_content_size_create} chars.")
            
            # Create parent directories if needed
            Path(norm_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(norm_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult.success(f"File created successfully: '{norm_path}'")
            
        except Exception as e:
            return ToolResult.error(f"Error creating file '{args.get('file_path', 'unknown')}': {str(e)}")


class CreateMultipleFilesTool(BaseTool):
    """Handle create_multiple_files function calls."""
    
    def get_name(self) -> str:
        return "create_multiple_files"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute create_multiple_files with validation."""
        created_files = []
        errors = []
        
        for file_info in args["files"]:
            try:
                norm_path = normalize_path(file_info["path"], self.config)
                content = file_info["content"]
                
                # Validate content size
                if len(content) > self.config.max_file_content_size_create:
                    errors.append(f"'{file_info['path']}': Content too large ({len(content)} chars)")
                    continue
                
                # Create parent directories if needed
                Path(norm_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(norm_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append(norm_path)
                
            except Exception as e:
                errors.append(f"'{file_info['path']}': {str(e)}")
        
        # Prepare response
        response_parts = []
        if created_files:
            response_parts.append(f"Successfully created {len(created_files)} files:")
            for file_path in created_files:
                response_parts.append(f"  - {file_path}")
        
        if errors:
            response_parts.append(f"\nErrors ({len(errors)}):")
            for error in errors:
                response_parts.append(f"  - {error}")
        
        return ToolResult.success("\n".join(response_parts))


class EditFileTool(BaseTool):
    """Handle edit_file function calls."""
    
    def get_name(self) -> str:
        return "edit_file"
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute edit_file with fuzzy matching support."""
        try:
            norm_path = normalize_path(args["file_path"], self.config)
            original_snippet = args["original_snippet"]
            new_snippet = args["new_snippet"]
            
            # Apply the edit with fuzzy matching
            apply_fuzzy_diff_edit(norm_path, original_snippet, new_snippet, self.config)
            
            return ToolResult.success(f"File edited successfully: '{norm_path}'")
            
        except Exception as e:
            return ToolResult.error(f"Error editing file '{args.get('file_path', 'unknown')}': {str(e)}")


def create_file_tools(config) -> list[BaseTool]:
    """Create all file tools."""
    return [
        ReadFileTool(config),
        ReadMultipleFilesTool(config),
        CreateFileTool(config),
        CreateMultipleFilesTool(config),
        EditFileTool(config)
    ]