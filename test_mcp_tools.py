#!/usr/bin/env python3
"""
Test script to verify MCP server tools are working correctly.
This script tests the server can start and tools are registered properly.
"""

import sys
import json
from pathlib import Path

def test_import():
    """Test that the server can be imported without errors"""
    print("1. Testing server import...")
    try:
        from void_mcp_server import mcp, security
        print("   ✓ Server imported successfully")
        print(f"   ✓ Server name: {mcp.name}")
        print(f"   ✓ Allowed root: {security.allowed_root}")
        return mcp
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        sys.exit(1)

def test_tools_registered(mcp):
    """Test that all expected tools are registered"""
    print("\n2. Testing tool registration...")

    expected_tools = [
        "read_file",
        "write_file",
        "create_file",
        "delete_file",
        "list_directory",
        "create_directory",
        "move_file",
        "search_in_files"
    ]

    try:
        # Access the internal tools registry
        if hasattr(mcp, '_tools'):
            registered = list(mcp._tools.keys())
            print(f"   ✓ Found {len(registered)} registered tools")

            for tool_name in expected_tools:
                if tool_name in registered:
                    print(f"   ✓ {tool_name}")
                else:
                    print(f"   ✗ {tool_name} - NOT FOUND")

            # Check for unexpected tools
            extra = set(registered) - set(expected_tools)
            if extra:
                print(f"   ! Extra tools found: {extra}")

            return True
        else:
            print("   ! Cannot access internal tool registry")
            return False

    except Exception as e:
        print(f"   ✗ Tool registration check failed: {e}")
        return False

def test_tool_metadata(mcp):
    """Test that tools have proper metadata"""
    print("\n3. Testing tool metadata...")

    try:
        if hasattr(mcp, '_tools'):
            tools = mcp._tools

            # Check a sample tool for metadata
            sample_tools = ["read_file", "write_file", "delete_file"]

            for tool_name in sample_tools:
                if tool_name in tools:
                    tool = tools[tool_name]
                    print(f"\n   {tool_name}:")

                    # Check if tool has callable function
                    if callable(tool):
                        print(f"     ✓ Is callable")
                    else:
                        print(f"     ✗ Not callable")

                    # Check for annotations (if accessible)
                    if hasattr(tool, '__name__'):
                        print(f"     ✓ Function name: {tool.__name__}")

                    if hasattr(tool, '__doc__'):
                        doc = tool.__doc__
                        if doc:
                            first_line = doc.strip().split('\n')[0]
                            print(f"     ✓ Docstring: {first_line[:60]}...")
                        else:
                            print(f"     ! No docstring")

            return True
        else:
            print("   ! Cannot access tool metadata")
            return False

    except Exception as e:
        print(f"   ✗ Metadata check failed: {e}")
        return False

def test_security_config():
    """Test security configuration is loaded"""
    print("\n4. Testing security configuration...")

    try:
        from void_mcp_server import security

        print(f"   ✓ Allowed root: {security.allowed_root}")
        print(f"   ✓ Max file size: {security.max_file_size / (1024*1024):.1f} MB")
        print(f"   ✓ Blocked patterns: {len(security.blocked_patterns)} patterns")
        print(f"   ✓ Allowed extensions: {len(security.allowed_extensions)} extensions")

        # Test a sample path validation
        test_path = "test.py"
        allowed, reason = security.is_path_allowed(test_path)
        print(f"\n   Test path validation for '{test_path}':")
        print(f"     {'✓' if allowed else '✗'} {reason}")

        return True

    except Exception as e:
        print(f"   ✗ Security config check failed: {e}")
        return False

def test_tool_schemas(mcp):
    """Test that tools can generate proper JSON schemas"""
    print("\n5. Testing tool schema generation...")

    try:
        # This tests that FastMCP can introspect the functions
        # and generate proper MCP tool schemas

        # Try to simulate what MCP does when listing tools
        if hasattr(mcp, 'list_tools'):
            print("   ✓ Server has list_tools method")

        if hasattr(mcp, '_tools'):
            print(f"   ✓ Can access {len(mcp._tools)} tool definitions")

            # Check if we can get function signatures
            from inspect import signature

            sample = "read_file"
            if sample in mcp._tools:
                func = mcp._tools[sample]
                sig = signature(func)
                print(f"\n   {sample} signature: {sig}")
                print(f"     ✓ Parameters: {list(sig.parameters.keys())}")

                for param_name, param in sig.parameters.items():
                    annotation = param.annotation
                    if annotation != param.empty:
                        print(f"       - {param_name}: {annotation}")

        return True

    except Exception as e:
        print(f"   ✗ Schema generation check failed: {e}")
        return False

def test_annotations():
    """Test that tool annotations are properly configured"""
    print("\n6. Testing tool annotations...")

    try:
        from void_mcp_server import mcp
        from mcp.types import ToolAnnotations

        print("   ✓ ToolAnnotations imported successfully")

        # Test creating an annotation
        test_annotation = ToolAnnotations(
            readOnlyHint=True,
            idempotentHint=True
        )
        print(f"   ✓ Can create ToolAnnotations: {test_annotation}")

        return True

    except Exception as e:
        print(f"   ✗ Annotations check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Server Tool Testing")
    print("=" * 60)

    # Run tests
    mcp = test_import()
    test_tools_registered(mcp)
    test_tool_metadata(mcp)
    test_security_config()
    test_tool_schemas(mcp)
    test_annotations()

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the server: python void_mcp_server.py")
    print("2. Configure Void Editor to connect to the server")
    print("3. Test with your LLM in Void")
    print("\nIf using qwen3-coder:30b, try the enhanced System_prompt_enhanced.txt")

if __name__ == "__main__":
    main()
