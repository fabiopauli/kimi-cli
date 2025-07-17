#!/usr/bin/env python3

"""
Tests for src.core.config module.

Tests the Config class and configuration management functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.config import Config


class TestConfig:
    """Test the Config class."""
    
    def test_config_initialization(self):
        """Test basic config initialization."""
        config = Config()
        
        # Check default values
        assert config.base_dir == Path.cwd()
        assert config.default_model == "grok-3"
        assert config.reasoner_model == "grok-4"
        assert config.fuzzy_enabled_by_default is False
        assert config.require_bash_confirmation is True
        assert config.require_powershell_confirmation is True
        
    def test_config_with_temp_dir(self, temp_dir):
        """Test config with custom base directory."""
        config = Config()
        config.set_base_dir(temp_dir)
        
        assert config.base_dir == temp_dir.resolve()
        
    def test_os_info_detection(self):
        """Test OS information detection."""
        config = Config()
        
        # OS info should be populated
        assert 'system' in config.os_info
        assert 'release' in config.os_info
        assert 'python_version' in config.os_info
        assert 'shell_available' in config.os_info
        
        # Should have boolean flags
        assert isinstance(config.os_info['is_windows'], bool)
        assert isinstance(config.os_info['is_mac'], bool)
        assert isinstance(config.os_info['is_linux'], bool)
        
    def test_model_switching(self):
        """Test model switching functionality."""
        config = Config()
        
        # Test switching to reasoner
        config.set_model("grok-4")
        assert config.current_model == "grok-4"
        assert config.is_reasoner is True
        
        # Test switching back to default
        config.set_model("grok-3")
        assert config.current_model == "grok-3"
        assert config.is_reasoner is False
        
    def test_git_context_management(self):
        """Test git context enable/disable."""
        config = Config()
        
        # Initially disabled
        assert config.git_enabled is False
        assert config.git_branch is None
        
        # Enable git
        config.enable_git(branch="main", skip_staging=True)
        assert config.git_enabled is True
        assert config.git_branch == "main"
        assert config.git_skip_staging is True
        
        # Disable git
        config.disable_git()
        assert config.git_enabled is False
        assert config.git_branch is None
        assert config.git_skip_staging is False
        
    def test_max_tokens_for_model(self):
        """Test token limit retrieval for different models."""
        config = Config()
        
        # Test known models
        assert config.get_max_tokens_for_model("grok-3") == 128000
        assert config.get_max_tokens_for_model("grok-4") == 128000
        
        # Test unknown model (should return default)
        assert config.get_max_tokens_for_model("unknown-model") == 128000
        
    def test_file_exclusions(self):
        """Test file exclusion patterns."""
        config = Config()
        
        # Should have default exclusions
        assert ".DS_Store" in config.excluded_files
        assert ".git" in config.excluded_files
        assert "__pycache__" in config.excluded_files
        
        assert ".pyc" in config.excluded_extensions
        assert ".png" in config.excluded_extensions
        assert ".log" in config.excluded_extensions
        
    @patch('builtins.open', new_callable=mock_open, read_data='{"models": {"default_model": "custom-grok"}}')
    @patch('pathlib.Path.exists', return_value=True)
    def test_config_file_loading(self, mock_exists, mock_file):
        """Test loading configuration from file."""
        config = Config()
        
        # Should load custom model from config
        assert config.default_model == "custom-grok"
        
    def test_system_prompt_generation(self):
        """Test system prompt generation."""
        config = Config()
        prompt = config.get_system_prompt()
        
        # Should contain expected content
        assert "Kimi Engineer" in prompt
        assert config.os_info['system'] in prompt
        assert "Capabilities" in prompt
        
    def test_tools_generation(self):
        """Test tool definitions."""
        config = Config()
        tools = config.get_tools()
        
        # Should have expected tools
        tool_names = [tool.function.name for tool in tools]
        expected_tools = [
            "read_file", "read_multiple_files", "create_file", 
            "create_multiple_files", "edit_file", "run_bash", "run_powershell"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names


class TestConfigWithFiles:
    """Test Config class with file operations."""
    
    def test_config_file_not_found(self):
        """Test behavior when config file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            config = Config()
            # Should use defaults when file doesn't exist
            assert config.default_model == "grok-3"
            
    def test_invalid_config_file(self):
        """Test behavior with invalid JSON config."""
        with patch('builtins.open', new_callable=mock_open, read_data='invalid json'):
            with patch('pathlib.Path.exists', return_value=True):
                config = Config()
                # Should use defaults when JSON is invalid
                assert config.default_model == "grok-3"
                
    def test_partial_config_file(self):
        """Test behavior with partial config file."""
        partial_config = {
            "file_limits": {"max_files_in_add_dir": 500},
            "security": {"require_bash_confirmation": False}
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(partial_config)):
            with patch('pathlib.Path.exists', return_value=True):
                config = Config()
                
                # Should apply partial config
                assert config.max_files_in_add_dir == 500
                assert config.require_bash_confirmation is False
                
                # Should keep defaults for unspecified values
                assert config.default_model == "grok-3"


@pytest.mark.security
class TestConfigSecurity:
    """Test security-related configuration."""
    
    def test_fuzzy_matching_disabled_by_default(self):
        """Test that fuzzy matching is disabled by default for security."""
        config = Config()
        assert config.fuzzy_enabled_by_default is False
        
    def test_confirmation_enabled_by_default(self):
        """Test that shell confirmations are enabled by default."""
        config = Config()
        assert config.require_bash_confirmation is True
        assert config.require_powershell_confirmation is True
        
    def test_base_dir_security(self, temp_dir):
        """Test base directory security."""
        config = Config()
        
        # Should resolve to absolute path
        config.set_base_dir(temp_dir)
        assert config.base_dir.is_absolute()
        assert config.base_dir == temp_dir.resolve()


@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for Config class."""
    
    def test_config_with_real_file_system(self, temp_dir):
        """Test config with real file system operations."""
        # Create a real config file
        config_file = temp_dir / "config.json"
        config_data = {
            "models": {"default_model": "test-model"},
            "fuzzy_matching": {"enabled_by_default": True},
            "excluded_files": ["test.tmp"]
        }
        config_file.write_text(json.dumps(config_data))
        
        # Point config to our test file
        with patch.object(Path, 'parent', new_callable=lambda: temp_dir):
            config = Config()
            
            # Verify config was loaded (would need to manually trigger reload)
            # This is a simplified test since the actual loading happens in __post_init__