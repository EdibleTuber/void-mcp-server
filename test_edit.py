#!/usr/bin/env python3
"""
Test script for edit_file tool
"""

import sys
from pathlib import Path

# Import the server
from mcp_server import edit_file, create_file, read_file, delete_file

def test_basic_edit():
    """Test 1: Basic single replacement"""
    print("Test 1: Basic single replacement...")

    # Create test file
    create_file("test_basic.txt", "x = 1\ny = 2\nz = 3")

    # Edit it
    result = edit_file("test_basic.txt", "x = 1", "x = 10")
    print(f"  Result: {result}")

    # Verify
    content = read_file("test_basic.txt")
    assert content == "x = 10\ny = 2\nz = 3", f"Expected 'x = 10\\ny = 2\\nz = 3', got '{content}'"
    print("  ✓ PASSED")

    # Cleanup
    delete_file("test_basic.txt")

def test_not_found():
    """Test 2: Text not found"""
    print("\nTest 2: Text not found...")

    create_file("test_notfound.txt", "hello world")
    result = edit_file("test_notfound.txt", "goodbye", "farewell")

    assert "not found" in result.lower(), f"Expected 'not found' error, got: {result}"
    print(f"  Result: {result}")
    print("  ✓ PASSED")

    delete_file("test_notfound.txt")

def test_ambiguous():
    """Test 3: Ambiguous match (appears multiple times)"""
    print("\nTest 3: Ambiguous match...")

    create_file("test_ambiguous.txt", "x = 1\nx = 2\nx = 3")
    result = edit_file("test_ambiguous.txt", "x = ", "y = ")

    assert "appears" in result.lower() and "times" in result.lower(), f"Expected ambiguous error, got: {result}"
    print(f"  Result: {result}")
    print("  ✓ PASSED")

    delete_file("test_ambiguous.txt")

def test_replace_all():
    """Test 4: Replace all occurrences"""
    print("\nTest 4: Replace all occurrences...")

    create_file("test_replace_all.txt", "x = 1\nx = 2\nx = 3")
    result = edit_file("test_replace_all.txt", "x = ", "y = ", replace_all=True)

    print(f"  Result: {result}")
    content = read_file("test_replace_all.txt")
    assert content == "y = 1\ny = 2\ny = 3", f"Expected all 'x' replaced with 'y', got: {content}"
    assert "3 occurrence" in result, f"Expected '3 occurrence(s)', got: {result}"
    print("  ✓ PASSED")

    delete_file("test_replace_all.txt")

def test_multiline():
    """Test 5: Multiline replacement"""
    print("\nTest 5: Multiline replacement...")

    content = """def foo():
    pass

def bar():
    pass"""

    create_file("test_multiline.txt", content)

    result = edit_file(
        "test_multiline.txt",
        "def foo():\n    pass",
        "def foo():\n    return 42"
    )

    print(f"  Result: {result}")
    new_content = read_file("test_multiline.txt")
    assert "return 42" in new_content, f"Expected 'return 42' in content, got: {new_content}"
    assert "def bar():" in new_content, f"Expected 'def bar():' preserved, got: {new_content}"
    print("  ✓ PASSED")

    delete_file("test_multiline.txt")

def test_indentation_preserved():
    """Test 6: Indentation preserved"""
    print("\nTest 6: Indentation preserved...")

    content = """class X:
    def foo():
        pass"""

    create_file("test_indent.txt", content)

    result = edit_file(
        "test_indent.txt",
        "    def foo():\n        pass",
        "    def foo():\n        return 1"
    )

    print(f"  Result: {result}")
    new_content = read_file("test_indent.txt")
    assert "        return 1" in new_content, f"Expected 8-space indent preserved, got: {new_content}"
    print("  ✓ PASSED")

    delete_file("test_indent.txt")

def test_more_context_for_uniqueness():
    """Test 7: Adding context makes match unique"""
    print("\nTest 7: Adding context for uniqueness...")

    content = """def process(x):
    return x

class Handler:
    def process(x):
        return x * 2"""

    create_file("test_context.txt", content)

    # First try: ambiguous
    result1 = edit_file("test_context.txt", "def process(x):", "def process(x, y):")
    assert "appears 2 times" in result1, f"Expected ambiguous error, got: {result1}"
    print(f"  Ambiguous attempt: {result1}")

    # Second try: with more context (unique)
    result2 = edit_file(
        "test_context.txt",
        "def process(x):\n    return x\n\nclass Handler:",
        "def process(x, y):\n    return x + y\n\nclass Handler:"
    )

    print(f"  With context: {result2}")
    assert "Successfully replaced" in result2, f"Expected success, got: {result2}"

    new_content = read_file("test_context.txt")
    assert "return x + y" in new_content, f"Expected 'return x + y', got: {new_content}"
    assert "return x * 2" in new_content, f"Expected second process() unchanged, got: {new_content}"
    print("  ✓ PASSED")

    delete_file("test_context.txt")

def test_file_not_found():
    """Test 8: File not found"""
    print("\nTest 8: File not found...")

    result = edit_file("nonexistent.txt", "old", "new")
    assert "not found" in result.lower(), f"Expected file not found error, got: {result}"
    print(f"  Result: {result}")
    print("  ✓ PASSED")

def main():
    print("=" * 60)
    print("Testing edit_file tool")
    print("=" * 60)

    try:
        test_basic_edit()
        test_not_found()
        test_ambiguous()
        test_replace_all()
        test_multiline()
        test_indentation_preserved()
        test_more_context_for_uniqueness()
        test_file_not_found()

        print("\n" + "=" * 60)
        print("All tests PASSED! ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
