# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a sandboxed MCP (Model Context Protocol) server that provides Void Editor with secure filesystem access. It's a single-file Python server (`void_mcp_server.py`) that exposes filesystem operations as MCP tools with multiple layers of security controls.

**GitHub Repository**: https://github.com/EdibleTuber/void-mcp-server

## Development Setup

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .void_venv
source .void_venv/bin/activate  # Linux/macOS
# .void_venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Server
```bash
# Direct execution (for testing)
python void_mcp_server.py

# Via Void Editor (configured in Void's MCP settings)
# See Directions.md for full configuration details
```

### Testing
```bash
# Run verification tests
python test_mcp_tools.py

# For future automated tests (if added)
pytest tests/
```

## Architecture

### Single-File Design
The entire server is contained in `void_mcp_server.py`. This intentional design keeps the security logic centralized and auditable.

### Security-First Architecture
All filesystem operations flow through the `SecurityConfig` class, which implements:

1. **Path Sandboxing**: All operations are restricted to `allowed_root` directory using `Path.resolve()` and relative path validation
2. **Pattern Blocking**: Blacklist approach for sensitive files/directories (.git, .env, .ssh, etc.)
3. **Extension Whitelisting**: Only specific text file extensions are allowed
4. **Size Limits**: 10MB default file size limit (configurable)

The security flow is:
```
MCP Tool Call → security.is_path_allowed() → Operation → Result
```

Every tool decorated with `@mcp.tool()` must call `security.is_path_allowed()` before any filesystem operation.

### Configuration System
The server loads configuration from `mcp_config.json` at startup via `SecurityConfig.load_config()`:
- If the file doesn't exist, defaults to current working directory
- Configuration is loaded once on initialization (not hot-reloadable)
- Custom blocked patterns and allowed extensions are merged with defaults

### MCP Tools vs Resources
- **Tools** (`@mcp.tool()`): Executable functions that perform filesystem operations (read_file, write_file, etc.)
- **Resources** (`@mcp.resource()`): Read-only data providers (security config, workspace info)

### Available Tools
The server exposes 8 filesystem tools:
- `read_file(path)` - Read file contents
- `write_file(path, content)` - Write/overwrite file
- `create_file(path, content="")` - Create new file (fails if exists)
- `delete_file(path)` - Delete file
- `list_directory(path=".")` - List directory contents
- `create_directory(path)` - Create directory
- `move_file(source, destination)` - Move/rename file
- `search_in_files(search_term, directory=".", file_pattern="*.py")` - Search files

### Error Handling Philosophy
All tools return string messages (never raise exceptions to MCP client):
- Success: Descriptive confirmation message
- Failure: Clear error message explaining what went wrong
- Security denial: Explicit reason for denial

## Key Implementation Details

### Path Resolution
All paths go through `Path.resolve()` to get absolute paths before validation. This prevents directory traversal attacks like `../../etc/passwd`.

### Security Validation
The `is_path_allowed()` method returns `(bool, str)` tuple:
- First element: whether operation is allowed
- Second element: human-readable reason (for logging/errors)

### File Extension Handling
Extension checking happens in `is_path_allowed()` for both existing files and files being created. The check is case-insensitive via `.lower()`.

### Search Implementation
`search_in_files()` validates each file individually during recursive search to prevent security bypasses. Results are limited to 50 matches to avoid overwhelming responses.

### Void Editor Integration
The server includes a heartbeat mechanism (10-second intervals) to help debug connection issues with Void Editor. The heartbeat runs in a daemon thread so it doesn't block shutdown.

## Configuration Notes

### mcp_config.json Structure
```json
{
  "allowed_root": "/absolute/path/to/project",
  "additional_blocked": ["patterns", "to", "block"],
  "additional_extensions": [".ext1", ".ext2"],
  "max_file_size_mb": 10
}
```

### Configuration Loading
The server looks for `mcp_config.json` in the same directory as `void_mcp_server.py`. The path is resolved using:
```python
_script_dir = Path(__file__).parent
_config_path = _script_dir / "mcp_config.json"
```

## Security Considerations

### What's Protected
- Path traversal attacks (via `Path.resolve()` and `relative_to()` checking)
- Access to sensitive files (.env, private keys, credentials)
- Access to VCS directories (.git)
- Binary file operations (extension whitelist)
- Large file operations (size limits)

### What's NOT Protected
- Race conditions between check and use (TOCTOU) - acceptable for this use case
- Symbolic link attacks - symlinks are not explicitly handled
- Resource exhaustion from many small files
- Concurrent modifications

### Adding New Tools
When adding new tools:
1. Always call `security.is_path_allowed()` first
2. Return descriptive string messages, not exceptions
3. Use `Path.resolve()` for all path operations
4. Use try/except to catch and return error messages
5. For file operations, check both source and destination paths
6. Add appropriate `ToolAnnotations` (readOnlyHint, destructiveHint, idempotentHint)

## Common Operations

### Extending Allowed Extensions
Edit `mcp_config.json`:
```json
{
  "additional_extensions": [".vue", ".svelte", ".sql"]
}
```

### Adding Custom Security Rules
Add to `additional_blocked` in `mcp_config.json`:
```json
{
  "additional_blocked": ["secrets", "credentials", ".aws"]
}
```

### Debugging Connection Issues
Check console output for:
- "Starting Void Sandboxed Filesystem MCP Server..."
- Process ID
- Periodic "[HH:MM:SS] Server alive" heartbeat messages

### Modifying the System Prompt
The repository includes two system prompt files:
- Basic: Simple tool descriptions (13 lines)
- `System_prompt_enhanced.txt`: Comprehensive guide with examples, workflows, and best practices (200+ lines)

For models with weaker tool-calling capabilities, use the enhanced prompt.

## File Organization

### Core Files
- `void_mcp_server.py` - Main server implementation (single file)
- `mcp_config.json` - Security and path configuration
- `requirements.txt` - Python dependencies

### Documentation
- `README.md` - User-facing documentation and setup guide
- `CLAUDE.md` - This file (development guide)
- `Directions.md` - Setup and configuration instructions
- `IMPROVEMENTS.md` - Change history and improvement rationale
- `WISHLIST.md` - Future feature requests

### Testing
- `test_mcp_tools.py` - Server verification script
- `test.txt` - Test artifact
- `file_create.test` - Test artifact

### Virtual Environment
- `.void_venv/` - Python virtual environment (gitignored)

## Development Workflow

### Making Changes to the Server
1. Activate virtual environment: `source .void_venv/bin/activate`
2. Edit `void_mcp_server.py`
3. Test locally: `python void_mcp_server.py` (verify it starts)
4. Run verification: `python test_mcp_tools.py`
5. Restart Void Editor to pick up changes

### Testing Security Rules
1. Modify `mcp_config.json` with new rules
2. Restart server (changes are loaded at startup only)
3. Test with paths that should be blocked/allowed
4. Verify error messages are clear

### Adding New MCP Tools
Example pattern:
```python
@mcp.tool(
    title="Short Title",
    description="Action-oriented description with usage hints",
    annotations=ToolAnnotations(
        readOnlyHint=True,  # or False
        destructiveHint=False,  # or True
        idempotentHint=True  # or False
    )
)
def tool_name(param: str) -> str:
    """Docstring for function"""
    # 1. Security check
    allowed, reason = security.is_path_allowed(param)
    if not allowed:
        return f"Access denied: {reason}"

    # 2. Path resolution
    try:
        abs_path = Path(param).resolve()

        # 3. Operation logic
        # ... your code here ...

        return "Success message"

    except Exception as e:
        return f"Error: {str(e)}"
```

## MCP Protocol Details

### Tool Registration
Tools are registered via the `@mcp.tool()` decorator from FastMCP. Each tool gets:
- `name` - Function name (e.g., "read_file")
- `title` - Human-readable name
- `description` - Usage guidance
- `inputSchema` - Auto-generated from type hints
- `annotations` - Semantic hints about behavior

### Resource Registration
Resources are registered via `@mcp.resource()` and provide read-only context:
- `security://config` - Current security settings
- `workspace://info` - Workspace statistics

### Server Lifecycle
1. Import loads `SecurityConfig` and reads `mcp_config.json`
2. Tools and resources are registered via decorators
3. `mcp.run()` starts the server and handles MCP protocol communication
4. Heartbeat thread runs in background for debugging

## Known Issues and Workarounds

### Void Editor Working Directory
Some versions of Void may not properly respect the `cwd` setting in MCP configuration. If you encounter "Path outside allowed directory" errors, ensure your project is located in a directory that Void can access.

### Model Compatibility
Tool-calling capability varies by model:
- **Excellent**: Claude 3.5 Sonnet, GPT-4, GPT-4o
- **Good**: Command-R+, Gemini 1.5 Pro, qwen2.5:32b-instruct (with enhanced prompt)
- **May need enhanced prompt**: DeepSeek Coder, CodeLlama
- **Not recommended**: qwen3-coder (code generation focused, poor tool-calling), smaller models (<13B)

**Tested Configuration**: qwen2.5:32b-instruct-q4_K_M with `System_prompt_enhanced.txt` provides good tool-calling performance for local development.

For models with weaker tool-calling capabilities, always use `System_prompt_enhanced.txt` which includes explicit examples and workflows.
