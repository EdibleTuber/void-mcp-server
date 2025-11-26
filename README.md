# Void MCP Filesystem Server

A secure, sandboxed MCP (Model Context Protocol) server that provides Void Editor with safe filesystem access. Enable your AI to create, read, modify, and delete files within your project—all with comprehensive security controls.

## Features

✅ **File Operations** - Create, read, write, delete, and move files  
✅ **Directory Management** - Create and list directories  
✅ **Search Capability** - Find text across multiple files  
✅ **Security Sandboxing** - Restricted paths, blocked extensions, size limits  
✅ **Easy Setup** - Simple configuration with JSON  
✅ **Error Handling** - Clear feedback on operations  

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Void Editor
- `pip` (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/void-mcp-filesystem-server.git
cd void-mcp-filesystem-server
```

2. **Create a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or on Windows:
# .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create configuration file** (optional)
```bash
cp mcp_config.example.json mcp_config.json
# Edit mcp_config.json with your settings
```

### Configure Void Editor

#### Option 1: Via Void Settings UI
1. Open Void Editor
2. Go to Settings/Preferences
3. Find the MCP Configuration section
4. Add your server:
   - **Command:** `/path/to/.venv/bin/python3`
   - **Args:** `["/full/path/to/mcp_server.py"]`
   - **Working Directory:** Your project root

#### Option 2: Edit MCP Config File
Create or edit the MCP servers config file:

**macOS/Linux:** `~/.config/void/mcp_servers.json`  
**Windows:** `%APPDATA%\void\mcp_servers.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "/absolute/path/to/.venv/bin/python3",
      "args": ["/absolute/path/to/mcp_server.py"],
      "cwd": "/your/project/directory"
    }
  }
}
```

**Important:** Use absolute paths for both the Python executable and script.

### Add System Prompt to Void

In Void's settings, find the prompt/instructions section and add:

```
You have access to filesystem tools via the MCP (Model Context Protocol) server. Use them to create, read, modify, and delete files as requested by the user.

Available tools:
- read_file(path: str) - Read file contents
- write_file(path: str, content: str) - Write or overwrite a file
- create_file(path: str, content: str = "") - Create a new file (fails if exists)
- delete_file(path: str) - Delete a file
- list_directory(path: str = ".") - List directory contents
- create_directory(path: str) - Create a directory
- move_file(source: str, destination: str) - Move or rename a file
- search_in_files(search_term: str, directory: str = ".", file_pattern: str = "*.py") - Search for text in files

When calling these tools, use the exact function name and parameters. Paths can be relative or absolute (if within project). Always use forward slashes (/) in paths.

Examples:
- Create: create_file("src/utils.py", "def helper():\n    pass")
- Read: read_file("src/main.py")
- Modify: First read_file(), then write_file() with updated content
- Search: search_in_files("TODO", "src", "*.py")
```

## Usage

Once configured, in Void's Agent Mode, ask your AI to perform file operations:

- "Create a new Python file at `src/handlers.py` with basic structure"
- "Read `config.json` and explain its structure"
- "Update `main.py` to add error handling"
- "Search for all TODO comments in the codebase"
- "Create a `tests/` directory and add a test file"

## Configuration

Edit `mcp_config.json` to customize security settings:

```json
{
  "allowed_root": "/absolute/path/to/your/project",
  "additional_blocked": [
    "secrets",
    "credentials"
  ],
  "additional_extensions": [
    ".vue",
    ".svelte"
  ],
  "max_file_size_mb": 10
}
```

### Configuration Options

- **`allowed_root`** - Project directory where operations are restricted (default: current directory)
- **`additional_blocked`** - Extra patterns to block (beyond defaults like .git, .env, .ssh)
- **`additional_extensions`** - Additional file extensions to allow
- **`max_file_size_mb`** - Maximum file size in megabytes (default: 10)

## Security

The server implements multiple layers of protection:

### Path Restrictions
- All operations confined to `allowed_root` directory
- No directory traversal attacks (`../../../etc/passwd` blocked)
- Uses `Path.resolve()` for absolute path validation

### File Blocking
- Blocks sensitive files: `.env`, `.key`, `.pem`, `id_rsa`, etc.
- Blocks directories: `.git`, `.ssh`, `node_modules`, `__pycache__`
- Only allows specific text file extensions

### Size Limits
- Default 10MB file size limit
- Prevents memory issues from large file operations

### No Shell Access
- No subprocess or shell command execution
- Safe even if AI behaves unexpectedly

## Testing

Run the included test suite to verify all functionality:

1. Create a test directory: `mkdir test_workspace && cd test_workspace`
2. Configure MCP to use this directory
3. Follow the test cases in [TEST_CASES.md](TEST_CASES.md)

Each test verifies a specific tool and includes security tests.

## Troubleshooting

### Server Won't Start
```bash
# Check Python version
python3 --version  # Must be 3.10+

# Check mcp is installed
pip list | grep mcp

# Try running manually
python3 mcp_server.py
```

### Void Can't Connect
- Verify paths in MCP config are absolute
- Check Python interpreter path is correct
- Ensure working directory exists
- Check Void's developer console for errors

### LLM Won't Use Tools
- Verify system prompt was added to Void settings
- Check that MCP server appears connected (look for tool icon)
- Try restarting Void
- Confirm model supports tool use (Claude, GPT-4, Command-R+ work best)

### Access Denied Errors - "Path outside allowed directory"

⚠️ **Known Void Issue:** Void currently restricts MCP servers to the Void installation directory, ignoring the `cwd` setting in `mcp.json`. This is a bug in Void's MCP channel implementation (see [Void GitHub Issue](#)).

**Workaround:** Place your project inside Void's installation directory:
```bash
# Move your project to Void's directory
mv /your/project/path /home/edible/Tools/Void/your_project
```

Then update `mcp_config.json`:
```json
{
  "allowed_root": "/home/edible/Tools/Void/your_project"
}
```

**Note:** This is a temporary workaround. The proper fix requires changes to Void's MCP implementation to respect the configured `cwd`.

### Other Access Denied Errors
- Check file/directory is within `allowed_root`
- Verify file extension is in allowed list
- Check if path contains blocked patterns (.git, .env, etc.)
- Review `mcp_config.json` settings

## Advanced Usage

### Custom Tool Prompts

In `mcp_server.py`, the system prompt is automatically provided via the `@mcp.prompt()` decorator. Modify this function to customize tool instructions for your use case.

### Extending Tools

Add new tools by creating functions with the `@mcp.tool()` decorator:

```python
@mcp.tool()
def count_lines(path: str) -> str:
    """Count lines in a file"""
    with open(path) as f:
        return str(len(f.readlines()))
```

### Adding Resources

Expose read-only data via `@mcp.resource()`:

```python
@mcp.resource("custom://data")
def get_custom_data() -> str:
    """Provide custom context data"""
    return "Custom data here"
```

## Limitations

- No symbolic link support
- No binary file operations
- No arbitrary command execution (intentional for security)
- 10MB file size limit (configurable)
- Operations slower than native filesystem access (network overhead)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing & Validation

Before submitting PRs:
- Run all test cases in `TEST_CASES.md`
- Test security constraints (path traversal, blocked extensions)
- Verify error messages are clear
- Check that operations work with different LLM models

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for [Void Editor](https://github.com/voideditor/void)
- Uses [Model Context Protocol (MCP)](https://modelcontextprotocol.io)
- Inspired by [Anthropic's MCP examples](https://github.com/modelcontextprotocol/python-sdk)

## Support

- 📚 [Void Editor Documentation](https://github.com/voideditor/void)
- 📖 [MCP Documentation](https://modelcontextprotocol.io)
- 🐛 [Report Issues](https://github.com/yourusername/void-mcp-filesystem-server/issues)

## Roadmap

- [ ] Backup/undo functionality
- [ ] Operation logging and audit trails
- [ ] Rate limiting
- [ ] Dry-run mode for previewing changes
- [ ] Git integration (auto-commit after changes)
- [ ] Multi-user support