# MCP Server Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Installation Steps

### 1. Create Virtual Environment

```bash
# Navigate to your project directory
cd /path/to/your/project

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install manually
pip install mcp
```

### 3. Verify Installation

```bash
# Check that mcp is installed
pip list | grep mcp

# Should show something like:
# mcp    1.x.x
```

### 4. Create Configuration File (Optional)

Create `mcp_config.json` in your project root:

```json
{
  "allowed_root": "/path/to/your/project",
  "additional_blocked": [],
  "additional_extensions": [],
  "max_file_size_mb": 10
}
```

### 5. Test Your Server

```bash
# Run the server
python your_mcp_server.py

# You should see:
# 🔒 Sandboxed MCP Server starting...
# 📁 Allowed root: /path/to/your/project
# ⚙️  Config file: mcp_config.json
```

## Configuring Void Editor

### Method 1: Via Void Settings

1. Open Void Editor
2. Go to Settings/Preferences
3. Find MCP Configuration section
4. Add your server:
   - **Command**: `python` (or full path to your venv python)
   - **Args**: `["/full/path/to/your_mcp_server.py"]`
   - **Working Directory**: Your project root

### Method 2: Via Configuration File

Create or edit Void's MCP config file (location varies by OS):

**macOS/Linux:** `~/.config/void/mcp_servers.json`  
**Windows:** `%APPDATA%\void\mcp_servers.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/your_mcp_server.py"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### Method 3: Using Virtual Environment

If using a virtual environment, make sure to use the venv's Python:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "/path/to/project/.venv/bin/python",
      "args": ["/path/to/project/mcp_server.py"],
      "cwd": "/path/to/project"
    }
  }
}
```

## Troubleshooting

### Server Won't Start

- Check Python version: `python --version` (should be 3.10+)
- Verify mcp is installed: `pip list | grep mcp`
- Check file permissions on your server script
- Ensure virtual environment is activated

### Void Can't Connect

- Check the command path in Void's config
- Verify the server script path is absolute
- Look at Void's developer console for error messages
- Try running the server manually to see if it starts

### Permission Errors

- Check `allowed_root` in `mcp_config.json`
- Verify file paths are within the allowed root
- Check file extensions are in the allowed list

## Development Tips

### Running Tests

```bash
# If you add tests later
pytest tests/
```

### Debugging

Add print statements in your server code - they'll show in the terminal or Void's output:

```python
print(f"🔍 Debug: Processing request for {path}")
```

### Hot Reload

You'll need to restart Void (or reload the MCP connection) after making changes to your server code.

## Security Checklist

- [ ] Set `allowed_root` to your project directory
- [ ] Review `blocked_patterns` - add any sensitive directories
- [ ] Verify `allowed_extensions` includes only text files
- [ ] Test with a non-critical project first
- [ ] Keep your `.venv` in `.gitignore`
- [ ] Don't commit `mcp_config.json` if it contains paths

## Next Steps

1. Test read operations first (list_directory, read_file, search_in_files)
2. Verify sandboxing works (try accessing files outside allowed_root)
3. Test write operations in a test directory
4. Set up git in your project for easy rollback
5. Customize the server with your own tools