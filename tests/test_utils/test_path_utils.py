#!/usr/bin/env python3

"""
Tests for src.utils.path_utils module.

Tests path normalization, validation, and directory operations.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.utils.path_utils import (
    normalize_path, get_directory_tree_summary, is_path_safe,
    get_relative_path, ensure_directory_exists, is_excluded_file
)


@pytest.mark.utils
class TestNormalizePath:
    """Test path normalization functionality."""
    
    def test_normalize_relative_path(self, mock_config, temp_dir):
        """Test normalization of relative paths."""
        mock_config.base_dir = temp_dir
        
        # Test relative path
        result = normalize_path("test.txt", mock_config)
        expected = str(temp_dir / "test.txt")
        assert result == expected
        
    def test_normalize_absolute_path(self, mock_config, temp_dir):
        """Test normalization of absolute paths within base dir."""
        mock_config.base_dir = temp_dir
        
        # Test absolute path within base dir
        test_file = temp_dir / "test.txt"
        result = normalize_path(str(test_file), mock_config)
        assert result == str(test_file)
        
    def test_normalize_path_outside_base_dir(self, mock_config, temp_dir):
        """Test security: path outside base directory should raise error."""
        mock_config.base_dir = temp_dir
        
        # Test path outside base directory
        outside_path = "/etc/passwd"
        with pytest.raises(ValueError, match="outside the base directory"):
            normalize_path(outside_path, mock_config)
            
    def test_normalize_path_with_traversal_attack(self, mock_config, temp_dir):
        """Test security: directory traversal attack should be blocked."""
        mock_config.base_dir = temp_dir
        
        # Test directory traversal
        with pytest.raises(ValueError, match="outside the base directory"):
            normalize_path("../../../etc/passwd", mock_config)
            
    def test_normalize_empty_path(self, mock_config):
        """Test handling of empty paths."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            normalize_path("", mock_config)
            
        with pytest.raises(ValueError, match="Path cannot be empty"):
            normalize_path("   ", mock_config)
            
    def test_normalize_path_allow_outside(self, mock_config):
        """Test allowing paths outside base directory when explicitly enabled."""
        outside_path = "/tmp/test.txt"
        result = normalize_path(outside_path, mock_config, allow_outside_project=True)
        assert result == str(Path(outside_path).resolve())


@pytest.mark.utils
class TestDirectoryTreeSummary:
    """Test directory tree summary generation."""
    
    def test_empty_directory(self, mock_config, temp_dir):
        """Test summary of empty directory."""
        mock_config.base_dir = temp_dir
        
        result = get_directory_tree_summary(temp_dir, mock_config)
        assert f"📁 {temp_dir.name}/" in result
        
    def test_directory_with_files(self, mock_config, sample_files, temp_dir):
        """Test summary of directory with files."""
        mock_config.base_dir = temp_dir
        
        result = get_directory_tree_summary(temp_dir, mock_config)
        
        # Should contain directory name
        assert f"📁 {temp_dir.name}/" in result
        
        # Should contain files (not excluded ones)
        assert "📄 test.py" in result
        assert "📄 readme.txt" in result
        assert "📄 config.json" in result
        
    def test_directory_with_subdirectories(self, mock_config, sample_files, temp_dir):
        """Test summary with nested directories."""
        mock_config.base_dir = temp_dir
        
        result = get_directory_tree_summary(temp_dir, mock_config)
        
        # Should contain subdirectory
        assert "📁 subdir/" in result
        assert "📄 nested.txt" in result
        
    def test_directory_max_depth(self, mock_config, temp_dir):
        """Test directory traversal depth limit."""
        mock_config.base_dir = temp_dir
        
        # Create deep directory structure
        deep_dir = temp_dir
        for i in range(5):
            deep_dir = deep_dir / f"level{i}"
            deep_dir.mkdir()
            (deep_dir / f"file{i}.txt").write_text(f"Level {i}")
        
        # Test with limited depth
        result = get_directory_tree_summary(temp_dir, mock_config, max_depth=2)
        
        # Should not go beyond max_depth
        assert "level0" in result
        assert "level1" in result
        # level2 might be present but level3+ should not
        
    def test_directory_max_entries(self, mock_config, temp_dir):
        """Test directory entry count limit."""
        mock_config.base_dir = temp_dir
        
        # Create many files
        for i in range(20):
            (temp_dir / f"file{i:02d}.txt").write_text(f"File {i}")
        
        result = get_directory_tree_summary(temp_dir, mock_config, max_entries=10)
        
        # Should be truncated
        assert "Truncated" in result or len(result.split('\n')) <= 15
        
    def test_nonexistent_directory(self, mock_config, temp_dir):
        """Test summary of non-existent directory."""
        nonexistent = temp_dir / "does_not_exist"
        result = get_directory_tree_summary(nonexistent, mock_config)
        
        assert "does not exist" in result
        
    def test_excluded_files_filtering(self, mock_config, temp_dir):
        """Test that excluded files are filtered out."""
        mock_config.base_dir = temp_dir
        mock_config.excluded_files = {".DS_Store", "__pycache__"}
        mock_config.excluded_extensions = {".pyc", ".log"}
        
        # Create files that should be excluded
        (temp_dir / ".DS_Store").write_text("mac file")
        (temp_dir / "__pycache__").mkdir()
        (temp_dir / "test.pyc").write_bytes(b"compiled python")
        (temp_dir / "debug.log").write_text("log file")
        (temp_dir / "keep.txt").write_text("keep this")
        
        result = get_directory_tree_summary(temp_dir, mock_config)
        
        # Should not contain excluded items
        assert ".DS_Store" not in result
        assert "__pycache__" not in result
        assert "test.pyc" not in result
        assert "debug.log" not in result
        
        # Should contain non-excluded items
        assert "keep.txt" in result


@pytest.mark.utils
class TestPathSafety:
    """Test path safety checks."""
    
    def test_safe_path_within_base(self, mock_config, temp_dir):
        """Test safe path within base directory."""
        mock_config.base_dir = temp_dir
        
        # Create a file
        test_file = temp_dir / "safe.txt"
        test_file.write_text("safe content")
        
        assert is_path_safe(str(test_file), mock_config) is True
        assert is_path_safe("safe.txt", mock_config) is True
        
    def test_unsafe_path_outside_base(self, mock_config, temp_dir):
        """Test unsafe path outside base directory."""
        mock_config.base_dir = temp_dir
        
        assert is_path_safe("/etc/passwd", mock_config) is False
        assert is_path_safe("../../../etc/passwd", mock_config) is False
        
    def test_path_safety_with_nonexistent_files(self, mock_config, temp_dir):
        """Test path safety with non-existent files."""
        mock_config.base_dir = temp_dir
        
        # Non-existent but safe path
        assert is_path_safe("nonexistent.txt", mock_config) is True
        
        # Non-existent and unsafe path
        assert is_path_safe("/nonexistent/path", mock_config) is False


@pytest.mark.utils
class TestRelativePath:
    """Test relative path calculation."""
    
    def test_get_relative_path_within_base(self, temp_dir):
        """Test relative path calculation for files within base."""
        test_file = temp_dir / "subdir" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("test")
        
        result = get_relative_path(test_file, temp_dir)
        assert result == str(Path("subdir") / "test.txt")
        
    def test_get_relative_path_outside_base(self, temp_dir):
        """Test relative path calculation for files outside base."""
        outside_file = Path("/tmp/outside.txt")
        
        result = get_relative_path(outside_file, temp_dir)
        # Should return absolute path when outside base
        assert result == str(outside_file.resolve())


@pytest.mark.utils
class TestEnsureDirectory:
    """Test directory creation."""
    
    def test_ensure_directory_exists_new(self, temp_dir):
        """Test creating a new directory."""
        new_dir = temp_dir / "new" / "nested" / "dir"
        
        ensure_directory_exists(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()
        
    def test_ensure_directory_exists_existing(self, temp_dir):
        """Test with existing directory."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()
        
        # Should not raise error
        ensure_directory_exists(existing_dir)
        
        assert existing_dir.exists()
        assert existing_dir.is_dir()


@pytest.mark.utils
class TestExcludedFiles:
    """Test file exclusion logic."""
    
    def test_excluded_by_name(self, mock_config, temp_dir):
        """Test files excluded by name."""
        mock_config.excluded_files = {".DS_Store", "Thumbs.db"}
        
        assert is_excluded_file(".DS_Store", mock_config) is True
        assert is_excluded_file("Thumbs.db", mock_config) is True
        assert is_excluded_file("normal.txt", mock_config) is False
        
    def test_excluded_by_extension(self, mock_config, temp_dir):
        """Test files excluded by extension."""
        mock_config.excluded_extensions = {".pyc", ".log", ".tmp"}
        
        assert is_excluded_file("test.pyc", mock_config) is True
        assert is_excluded_file("debug.log", mock_config) is True
        assert is_excluded_file("temp.tmp", mock_config) is True
        assert is_excluded_file("source.py", mock_config) is False
        
    def test_case_insensitive_extension(self, mock_config):
        """Test case-insensitive extension matching."""
        mock_config.excluded_extensions = {".log"}
        
        # Should be case-insensitive
        assert is_excluded_file("test.LOG", mock_config) is True
        assert is_excluded_file("test.Log", mock_config) is True


@pytest.mark.security
class TestPathSecurityFeatures:
    """Test security features of path utilities."""
    
    def test_directory_traversal_prevention(self, mock_config, temp_dir):
        """Test prevention of directory traversal attacks."""
        mock_config.base_dir = temp_dir
        
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "subdir/../../../etc/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(ValueError):
                normalize_path(dangerous_path, mock_config)
                
    def test_symlink_handling(self, mock_config, temp_dir):
        """Test handling of symbolic links."""
        if hasattr(Path, 'symlink_to'):  # Unix-like systems
            mock_config.base_dir = temp_dir
            
            # Create a file outside base dir
            outside_file = Path("/tmp/outside.txt")
            if outside_file.parent.exists():
                outside_file.write_text("outside content")
                
                # Create symlink inside base dir pointing outside
                symlink = temp_dir / "dangerous_link"
                try:
                    symlink.symlink_to(outside_file)
                    
                    # Should be blocked
                    with pytest.raises(ValueError):
                        normalize_path(str(symlink), mock_config)
                except (OSError, NotImplementedError):
                    # Skip if symlinks not supported
                    pytest.skip("Symlinks not supported on this system")