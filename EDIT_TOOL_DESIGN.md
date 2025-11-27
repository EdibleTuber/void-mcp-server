# Edit File Tool - Design Document

## Overview

Add precise file editing capability similar to Claude Code's Edit tool.

## Current Problem

```python
# To change one line, you must:
content = read_file("app.py")  # Read entire 500-line file
# Modify content (error-prone if LLM hallucinates)
write_file("app.py", modified_content)  # Write entire file back
```

**Issues**:
- Wastes tokens sending entire file
- Error-prone (LLM might change unrelated code)
- No validation that old_text actually exists
- Harder for LLM to get right

## Proposed Solution

```python
# Precise edit - find and replace specific text
edit_file(
    path="app.py",
    old_string="def process(data):\n    return data",
    new_string="def process(data):\n    return data.strip()"
)
```

**Benefits**:
- ✅ Uses fewer tokens (just the change)
- ✅ Validates old_string exists
- ✅ Fails safely if text not found or ambiguous
- ✅ Preserves exact indentation/formatting
- ✅ LLM less likely to make mistakes

---

## Tool Specification

### Basic Edit Tool

```python
@mcp.tool(
    title="Edit File",
    description="Make precise edits to a file by replacing exact text. Preserves formatting and indentation. Safer than rewriting entire file.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True
    )
)
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False
) -> str:
    """
    Edit a file by replacing exact text matches.

    Args:
        file_path: Path to file to edit
        old_string: Exact text to find and replace (must match exactly including whitespace)
        new_string: Replacement text
        replace_all: If True, replace all occurrences. If False (default), old_string must be unique.

    Returns:
        Success message or error description

    Examples:
        # Replace a function
        edit_file(
            "app.py",
            "def hello():\\n    print('hi')",
            "def hello():\\n    print('Hello, World!')"
        )

        # Update a variable
        edit_file(
            "config.py",
            "DEBUG = True",
            "DEBUG = False"
        )
    """
```

---

## Implementation Details

### Security Checks
```python
def edit_file(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    # 1. Security validation
    allowed, reason = security.is_path_allowed(file_path)
    if not allowed:
        return f"Access denied: {reason}"

    # 2. File existence check
    abs_path = Path(file_path).resolve()
    if not abs_path.exists():
        return f"File not found: {file_path}"

    if not abs_path.is_file():
        return f"Not a file: {file_path}"

    # 3. Size check
    size_ok, size_reason = security.check_file_size(str(abs_path))
    if not size_ok:
        return size_reason

    # ... proceed with edit
```

### Edit Logic

```python
    # 4. Read file
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return f"File appears to be binary: {file_path}"

    # 5. Validate old_string exists
    if old_string not in content:
        return f"Error: old_string not found in {file_path}"

    # 6. Check uniqueness (if not replace_all)
    if not replace_all:
        count = content.count(old_string)
        if count == 0:
            return f"Error: old_string not found in {file_path}"
        elif count > 1:
            return (
                f"Error: old_string appears {count} times in {file_path}. "
                f"Use replace_all=True to replace all occurrences, or provide "
                f"more context to make old_string unique."
            )

    # 7. Perform replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacements = content.count(old_string)
    else:
        new_content = content.replace(old_string, new_string, 1)
        replacements = 1

    # 8. Write back
    try:
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return f"Error writing file: {str(e)}"

    # 9. Success message
    rel_path = abs_path.relative_to(security.allowed_root)
    return f"Successfully replaced {replacements} occurrence(s) in {rel_path}"
```

---

## Error Handling

### Case 1: Text Not Found
```python
edit_file("app.py", "def foo():", "def bar():")
# Returns: "Error: old_string not found in app.py"
```

**Why**: Prevents silent failures. LLM must read file first to know exact text.

### Case 2: Ambiguous Match
```python
# File contains:
#   def process(x): return x
#   def process(x): return x * 2

edit_file("app.py", "def process(x): return x", "def process(x): return x + 1")
# Returns: "Error: old_string appears 2 times in app.py. Use replace_all=True or provide more context."
```

**Why**: Forces precision. LLM must include surrounding context:
```python
# Correct approach - include more context
edit_file(
    "app.py",
    "def process(x): return x\n\nclass Handler:",  # More context
    "def process(x): return x + 1\n\nclass Handler:"
)
```

### Case 3: Replace All
```python
edit_file("app.py", "TODO", "DONE", replace_all=True)
# Returns: "Successfully replaced 15 occurrence(s) in app.py"
```

**Use Case**: Renaming variables, updating strings

---

## Usage Patterns

### Pattern 1: Single Function Edit
```python
# 1. LLM reads file to see current state
content = read_file("utils.py")

# 2. LLM makes precise edit
edit_file(
    "utils.py",
    old_string="""def calculate(x, y):
    return x + y""",
    new_string="""def calculate(x, y):
    \"\"\"Add two numbers.\"\"\"
    return x + y"""
)
```

### Pattern 2: Multi-line Edit
```python
edit_file(
    "config.py",
    old_string="""DATABASE = {
    'host': 'localhost',
    'port': 5432
}""",
    new_string="""DATABASE = {
    'host': 'localhost',
    'port': 5432,
    'name': 'myapp'
}"""
)
```

### Pattern 3: Rename Variable (Globally)
```python
# Rename 'user_id' to 'account_id' everywhere
edit_file(
    "models.py",
    old_string="user_id",
    new_string="account_id",
    replace_all=True
)
```

---

## Integration with Existing Tools

### When to Use edit_file vs write_file

**Use `edit_file`**:
- Modifying existing file
- Changing small sections
- Want validation that text exists
- Multiple small changes to same file

**Use `write_file`**:
- Creating new file
- Complete rewrite
- File content generated from scratch
- Templating scenarios

**Use `create_file`**:
- New file that shouldn't exist yet
- Want error if file already exists

---

## Testing Plan

### Test 1: Basic Edit
```python
# Setup
create_file("test.py", "x = 1\ny = 2")

# Test
result = edit_file("test.py", "x = 1", "x = 10")

# Verify
assert result.startswith("Successfully replaced")
assert read_file("test.py") == "x = 10\ny = 2"
```

### Test 2: Not Found
```python
result = edit_file("test.py", "z = 3", "z = 30")
assert "not found" in result.lower()
```

### Test 3: Ambiguous
```python
create_file("test.py", "x = 1\nx = 2")
result = edit_file("test.py", "x = ", "x = 10")
assert "appears 2 times" in result
```

### Test 4: Replace All
```python
create_file("test.py", "x = 1\nx = 2\nx = 3")
result = edit_file("test.py", "x = ", "y = ", replace_all=True)
assert read_file("test.py") == "y = 1\ny = 2\ny = 3"
```

### Test 5: Multiline
```python
create_file("test.py", "def foo():\n    pass\n\ndef bar():\n    pass")
result = edit_file(
    "test.py",
    "def foo():\n    pass",
    "def foo():\n    return 42"
)
assert "return 42" in read_file("test.py")
```

### Test 6: Indentation Preserved
```python
create_file("test.py", "class X:\n    def foo():\n        pass")
result = edit_file(
    "test.py",
    "    def foo():\n        pass",
    "    def foo():\n        return 1"
)
content = read_file("test.py")
assert "        return 1" in content  # Preserves 8-space indent
```

---

## Future Enhancements (Not Now)

### Line-Based Editing (Later)
```python
def edit_file_lines(file_path: str, start_line: int, end_line: int, new_content: str):
    """Replace lines N through M with new content"""
```

**Pros**: Works well for specific line ranges
**Cons**: Line numbers change as file is edited (error-prone)

**Decision**: Start with text-based, add line-based only if needed

### Diff Preview (Later)
```python
def preview_edit(file_path: str, old_string: str, new_string: str) -> str:
    """Show what would change without actually changing it"""
    # Returns unified diff
```

**Decision**: Add if users request it

### Undo Support (Later)
```python
def undo_last_edit() -> str:
    """Revert the last edit operation"""
```

**Decision**: Add in Phase 6 (Error Recovery)

---

## Summary

**What we're building**:
- Precise find-and-replace file editing
- Validation that old_string exists and is unique
- Safety checks (security, encoding, size)
- Clear error messages

**What we're NOT building** (yet):
- Line-based editing
- Diff preview
- Undo/redo
- Multi-file batch edits

**Next Steps**:
1. Implement `edit_file` in `mcp_server.py`
2. Test thoroughly
3. Update documentation
4. Try it with LLM workflow

Ready to implement?
