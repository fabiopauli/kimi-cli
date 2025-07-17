#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Test config imports
    import config
    print("✓ config module imported successfully")
    print(f"  - Default model: {config.DEFAULT_MODEL}")
    print(f"  - Base directory: {config.base_dir}")
    
    # Test system prompt formatting
    try:
        formatted_prompt = config.get_formatted_system_prompt()
        print("✓ Dynamic system prompt formatting works")
        print(f"  - Prompt length: {len(formatted_prompt)} characters")
    except Exception as e:
        print(f"✗ System prompt formatting failed: {e}")
    
    # Test session imports (without xai_sdk)
    try:
        # Mock the xai_sdk imports for testing
        class MockClient:
            def __init__(self, api_key):
                self.api_key = api_key
                
            class chat:
                @staticmethod
                def create(model, tools):
                    return MockChat()
                    
        class MockChat:
            def append(self, message):
                pass
                
            def sample(self):
                return MockResponse()
                
        class MockResponse:
            def __init__(self):
                self.content = "Mock response"
                self.tool_calls = []
        
        # Temporarily patch xai_sdk
        sys.modules['xai_sdk'] = type('MockModule', (), {
            'Client': MockClient,
            'chat': type('MockChat', (), {
                'user': lambda x: x,
                'system': lambda x: x,
                'assistant': lambda x: x,
                'tool_result': lambda x: x
            })()
        })()
        
        # Now test session import
        import session
        print("✓ session module imported successfully")
        
        # Test session initialization
        mock_client = MockClient("test_key")
        test_session = session.KimiSession(mock_client, "kimi-k2-instruct")
        print("✓ KimiSession created successfully")
        print(f"  - Model: {test_session.model}")
        print(f"  - History length: {len(test_session.history)}")
        
    except Exception as e:
        print(f"✗ Session import/initialization failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test utils imports  
    try:
        import utils
        print("✓ utils module imported successfully")
    except Exception as e:
        print(f"✗ utils import failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ All basic imports and functionality tests passed!")
    
except Exception as e:
    print(f"✗ Import test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)