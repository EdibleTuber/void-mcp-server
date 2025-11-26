# MCP Server Improvements Summary

This document summarizes the improvements made to help with tool calling issues.

## Files Modified/Created

### 1. System_prompt_enhanced.txt (NEW)
**Size:** ~200 lines (vs 13 lines in original)

**What was added:**
- Concrete examples for every tool
- Common workflow patterns (create, modify, explore, search, delete)
- Parameter details for each tool
- Error handling guidance
- Best practices (DO/DON'T sections)
- Real usage examples in context

**Why it helps:**
- Models like qwen3-coder need explicit guidance and examples
- Shows HOW to use tools, not just WHAT they are
- Provides decision-making logic (when to use which tool)
- Includes multi-step workflows (read before write, etc.)

**To use:** Replace the content of System_prompt.txt with System_prompt_enhanced.txt, or point Void to use the enhanced version.

---

### 2. void_mcp_server.py (MODIFIED)
**Changes:**
- Added `from mcp.types import ToolAnnotations` import
- Enhanced all 8 `@mcp.tool()` decorators with:
  - `title` - Human-readable tool names
  - `description` - Action-oriented descriptions with usage hints
  - `annotations` - ToolAnnotations with semantic hints:
    - `readOnlyHint` - Marks safe read-only operations
    - `destructiveHint` - Marks dangerous operations (delete, overwrite)
    - `idempotentHint` - Marks operations safe to repeat

**Example before:**
```python
@mcp.tool()
def read_file(path: str) -> str:
    """Read contents of a file (with security checks)"""
```

**Example after:**
```python
@mcp.tool(
    title="Read File",
    description="Read and return the complete contents of a text file. Use this to examine existing files before modifying them.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True
    )
)
def read_file(path: str) -> str:
    """Read contents of a file (with security checks)"""
```

**Why it helps:**
- Better tool descriptions help models understand intent
- Semantic hints (readOnly, destructive) guide model decision-making
- MCP clients can use this metadata for better UX

---

### 3. test_mcp_tools.py (NEW)
**Purpose:** Verify the server configuration is correct

**Tests:**
- Server imports without errors
- Security configuration loads
- ToolAnnotations work correctly
- Server can start

**To use:**
```bash
source .void_venv/bin/activate
python test_mcp_tools.py
```

---

### 4. CLAUDE.md (UPDATED)
Removed incorrect reference to Void Editor sandboxing issue.

---

## Expected Impact

### High Impact (Most Likely to Help)
✅ **Enhanced System Prompt** - The biggest factor for tool calling success. The original 13-line prompt gave no examples or guidance. The 200-line enhanced version shows:
- Exact syntax for calling each tool
- When to use each tool
- Common workflows and patterns
- Error handling

### Medium Impact
✅ **Tool Annotations** - Makes tools more semantic and helps clients understand tool behavior. Some models pay attention to these hints.

### Diagnostic Value
✅ **Test Script** - Confirms server is configured correctly and can start.

---

## Testing Strategy

### Step 1: Verify Server Works
```bash
cd /home/edible/Projects/void_mcp_server
source .void_venv/bin/activate
python test_mcp_tools.py
```

Expected: All tests pass or show ✓

### Step 2: Start Server Manually
```bash
python void_mcp_server.py
```

Expected output:
```
Starting Void Sandboxed Filesystem MCP Server...
Allowed root: /home/edible/Tools/Void/projects/void_mcp_server
Config file: mcp_config.json
Server is running and waiting for connections...
Process ID: XXXXX
[HH:MM:SS] Server alive
```

### Step 3: Update Void Configuration
1. Copy content from `System_prompt_enhanced.txt`
2. In Void Editor settings, replace system prompt
3. Restart Void Editor

### Step 4: Test with qwen3-coder:30b
Try simple commands first:
- "List the files in the current directory"
- "Read the README file"
- "Create a test file called hello.txt with 'Hello World'"

### Step 5: Compare with Better Model (Optional)
If qwen3-coder still struggles, test with Claude 3.5 Sonnet or GPT-4 to isolate whether it's a model capability issue.

---

## Model Compatibility Assessment

### Known Good (High Tool-Calling Capability)
- ✅ Claude 3.5 Sonnet - Excellent
- ✅ GPT-4, GPT-4o - Excellent
- ✅ Command-R+ - Good
- ✅ Gemini 1.5 Pro - Good

### Needs Testing
- ⚠️ qwen3-coder:30b - **Your case** - Coding focused, may need more prompt guidance
- ⚠️ DeepSeek Coder - Coding focused, similar to Qwen
- ⚠️ CodeLlama - Older, may struggle

### Known Challenges
- ❌ Smaller models (<13B) - Often lack tool calling training
- ❌ Base models (non-instruct) - Not trained for tool use
- ❌ Pure completion models - Need instruction-tuned versions

---

## Troubleshooting Guide

### Issue: Model doesn't call any tools
**Check:**
1. Is the enhanced system prompt loaded?
2. Does Void show the MCP server as connected?
3. Try asking explicitly: "Use the list_directory tool to show files"

### Issue: Model calls wrong tool or wrong parameters
**Check:**
1. System prompt has clear examples
2. Try simpler requests first
3. Model may need stronger tool-calling capabilities

### Issue: Tools return errors
**Check:**
1. Server logs (terminal where server is running)
2. File paths are within allowed_root
3. File extensions are in allowed list

### Issue: Server won't start
**Check:**
1. Virtual environment activated
2. Dependencies installed: `pip install -r requirements.txt`
3. Python 3.10+ (`python --version`)

---

## If qwen3-coder Still Struggles

The enhanced prompt should help significantly, but if qwen3-coder:30b still has trouble:

1. **It's likely a model limitation** - Qwen Coder is optimized for code generation, not necessarily tool/function calling

2. **Options:**
   - Try a model with better tool-calling capability (Claude, GPT-4)
   - Simplify the request (one tool at a time)
   - Use more explicit language: "Call the read_file function with path parameter 'README.md'"

3. **Report back to Void/Qwen:**
   - This is useful feedback for improving model tool-calling support
   - Enhanced prompts help but can't fully compensate for missing training

---

## What Changed Under the Hood

**Tool Registration (MCP Protocol):**
```python
# Old way (minimal)
{
  "name": "read_file",
  "description": "Read contents of a file (with security checks)",
  "inputSchema": {...}
}

# New way (rich metadata)
{
  "name": "read_file",
  "title": "Read File",
  "description": "Read and return the complete contents of a text file. Use this to examine existing files before modifying them.",
  "inputSchema": {...},
  "annotations": {
    "readOnlyHint": true,
    "idempotentHint": true
  }
}
```

**System Prompt:**
- Old: Tool signatures only (13 lines)
- New: Examples, workflows, best practices (200+ lines)

This gives the model much more context about HOW and WHEN to use tools, not just WHAT they are.
