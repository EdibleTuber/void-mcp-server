"""
Sandboxed Filesystem MCP Server for Void Editor
Implements multiple layers of safety controls
"""

from mcp.server.fastmcp import FastMCP
import os
from pathlib import Path
from datetime import datetime
import json

# Initialize the MCP server
mcp = FastMCP("void-sandboxed-filesystem")

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

class SecurityConfig:
    """Centralized security configuration"""
    
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.allowed_root = None
        self.blocked_patterns = [
            '.git',
            '.env',
            '.ssh',
            'node_modules',
            '__pycache__',
            '.venv',
            'venv',
            '*.key',
            '*.pem',
            '*.p12',
            'id_rsa',
            'id_ed25519'
        ]
        self.allowed_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.c', '.cpp', '.h', '.hpp',
            '.go', '.rs', '.rb', '.php',
            '.html', '.css', '.scss', '.json',
            '.md', '.txt', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.xml'
        ]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.load_config()
    
    def load_config(self):
        """Load configuration from file if exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.allowed_root = config.get('allowed_root')
                    self.blocked_patterns.extend(config.get('additional_blocked', []))
                    self.allowed_extensions.extend(config.get('additional_extensions', []))
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        
        # Default to current working directory if not set
        if not self.allowed_root:
            self.allowed_root = os.getcwd()
    
    def is_path_allowed(self, path: str) -> tuple[bool, str]:
        """
        Check if a path is allowed based on security rules
        Returns: (is_allowed, reason)
        """
        try:
            # Resolve to absolute path
            abs_path = Path(path).resolve()
            allowed_root = Path(self.allowed_root).resolve()
            
            # Check if path is within allowed root
            try:
                abs_path.relative_to(allowed_root)
            except ValueError:
                return False, f"Path outside allowed directory: {allowed_root}"
            
            # Check for blocked patterns
            path_str = str(abs_path)
            for pattern in self.blocked_patterns:
                if pattern.startswith('*.'):
                    # Extension check
                    if path_str.endswith(pattern[1:]):
                        return False, f"Blocked file extension: {pattern}"
                else:
                    # Directory/file name check
                    if pattern in path_str.split(os.sep):
                        return False, f"Blocked pattern: {pattern}"
            
            # For file operations, check extension whitelist
            if abs_path.is_file() or not abs_path.exists():
                ext = abs_path.suffix.lower()
                if ext and ext not in self.allowed_extensions:
                    return False, f"File extension not allowed: {ext}"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    def check_file_size(self, path: str) -> tuple[bool, str]:
        """Check if file size is within limits"""
        try:
            size = os.path.getsize(path)
            if size > self.max_file_size:
                return False, f"File too large: {size} bytes (max: {self.max_file_size})"
            return True, "OK"
        except Exception as e:
            return False, f"Size check error: {str(e)}"


# Initialize security config
security = SecurityConfig()

# ============================================================================
# SAFE FILESYSTEM OPERATIONS
# ============================================================================

@mcp.tool()
def read_file(path: str) -> str:
    """Read contents of a file (with security checks)
    
    Args:
        path: Path to the file to read
    """
    allowed, reason = security.is_path_allowed(path)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        abs_path = Path(path).resolve()
        
        if not abs_path.exists():
            return f"File not found: {path}"
        
        if not abs_path.is_file():
            return f"Not a file: {path}"
        
        size_ok, size_reason = security.check_file_size(str(abs_path))
        if not size_ok:
            return size_reason
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except UnicodeDecodeError:
        return f"File appears to be binary or uses unsupported encoding: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file (with security checks)
    
    Args:
        path: Path to the file
        content: Content to write
    """
    allowed, reason = security.is_path_allowed(path)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        abs_path = Path(path).resolve()
        
        # Create parent directory if it doesn't exist
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if we're overwriting an existing file
        existed = abs_path.exists()
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        action = "Updated" if existed else "Created"
        rel_path = abs_path.relative_to(security.allowed_root)
        
        return f"{action} file: {rel_path}"
        
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def create_file(path: str, content: str = "") -> str:
    """Create a new file (fails if file exists)
    
    Args:
        path: Path to the file
        content: Initial content (optional)
    """
    allowed, reason = security.is_path_allowed(path)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        abs_path = Path(path).resolve()
        
        if abs_path.exists():
            return f"File already exists: {path}. Use write_file to update it."
        
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        rel_path = abs_path.relative_to(security.allowed_root)
        return f"Created file: {rel_path}"
        
    except Exception as e:
        return f"Error creating file: {str(e)}"


@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file (requires confirmation via explicit call)
    
    Args:
        path: Path to the file to delete
    """
    allowed, reason = security.is_path_allowed(path)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        abs_path = Path(path).resolve()
        
        if not abs_path.exists():
            return f"File not found: {path}"
        
        if not abs_path.is_file():
            return f"Not a file (use delete_directory for directories): {path}"
        
        abs_path.unlink()
        
        return f"Deleted file: {path}"
        
    except Exception as e:
        return f"Error deleting file: {str(e)}"


@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List contents of a directory
    
    Args:
        path: Directory path (default: current directory)
    """
    allowed, reason = security.is_path_allowed(path)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        abs_path = Path(path).resolve()
        
        if not abs_path.exists():
            return f"Directory not found: {path}"
        
        if not abs_path.is_dir():
            return f"Not a directory: {path}"
        
        items = list(abs_path.iterdir())
        files = [f for f in items if f.is_file()]
        dirs = [d for d in items if d.is_dir()]
        
        result = f"Directory: {abs_path.relative_to(security.allowed_root)}\n\n"
        
        if dirs:
            result += "Directories:\n"
            for d in sorted(dirs):
                result += f"  {d.name}\n"
        
        if files:
            result += "\nFiles:\n"
            for f in sorted(files):
                size = f.stat().st_size
                result += f"  {f.name} ({size} bytes)\n"
        
        if not dirs and not files:
            result += "(empty directory)\n"
        
        return result
        
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@mcp.tool()
def create_directory(path: str) -> str:
    """Create a new directory
    
    Args:
        path: Path of directory to create
    """
    allowed, reason = security.is_path_allowed(path)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        abs_path = Path(path).resolve()
        
        if abs_path.exists():
            return f"Directory already exists: {path}"
        
        abs_path.mkdir(parents=True, exist_ok=False)
        
        return f"Created directory: {abs_path.relative_to(security.allowed_root)}"
        
    except Exception as e:
        return f"Error creating directory: {str(e)}"


@mcp.tool()
def move_file(source: str, destination: str) -> str:
    """Move or rename a file
    
    Args:
        source: Current file path
        destination: New file path
    """
    src_allowed, src_reason = security.is_path_allowed(source)
    if not src_allowed:
        return f"Source access denied: {src_reason}"
    
    dst_allowed, dst_reason = security.is_path_allowed(destination)
    if not dst_allowed:
        return f"Destination access denied: {dst_reason}"
    
    try:
        src_path = Path(source).resolve()
        dst_path = Path(destination).resolve()
        
        if not src_path.exists():
            return f"Source file not found: {source}"
        
        if dst_path.exists():
            return f"Destination already exists: {destination}"
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.rename(dst_path)
        
        return f"Moved: {source} to {destination}"
        
    except Exception as e:
        return f"Error moving file: {str(e)}"


@mcp.tool()
def search_in_files(search_term: str, directory: str = ".", file_pattern: str = "*.py") -> str:
    """Search for a term in files (read-only)
    
    Args:
        search_term: Text to search for
        directory: Directory to search in
        file_pattern: File pattern (e.g., *.py, *.js)
    """
    allowed, reason = security.is_path_allowed(directory)
    if not allowed:
        return f"Access denied: {reason}"
    
    try:
        search_path = Path(directory).resolve()
        results = []
        
        for file_path in search_path.rglob(file_pattern):
            # Check each file individually
            file_allowed, _ = security.is_path_allowed(str(file_path))
            if not file_allowed:
                continue
                
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if search_term.lower() in line.lower():
                                rel_path = file_path.relative_to(search_path)
                                results.append(f"{rel_path}:{i}: {line.strip()}")
                except:
                    continue
        
        if results:
            count = len(results)
            limited = results[:50]
            output = "\n".join(limited)
            if count > 50:
                output += f"\n\n... and {count - 50} more results"
            return output
        
        return f"No matches found for '{search_term}'"
        
    except Exception as e:
        return f"Error searching files: {str(e)}"


@mcp.resource("security://config")
def security_config() -> str:
    """Display current security configuration"""
    config_info = f"""
Security Configuration:
======================
Allowed Root: {security.allowed_root}
Max File Size: {security.max_file_size / (1024*1024):.1f} MB

Blocked Patterns: {', '.join(security.blocked_patterns[:10])}
{f"... and {len(security.blocked_patterns) - 10} more" if len(security.blocked_patterns) > 10 else ""}

Allowed Extensions: {', '.join(security.allowed_extensions[:20])}
{f"... and {len(security.allowed_extensions) - 20} more" if len(security.allowed_extensions) > 20 else ""}
    """
    return config_info


@mcp.resource("workspace://info")
def workspace_info() -> str:
    """Get information about the current workspace"""
    try:
        root = Path(security.allowed_root)
        items = list(root.iterdir())
        files = sum(1 for f in items if f.is_file())
        dirs = sum(1 for d in items if d.is_dir())
        
        return f"""
Workspace: {root}
Files: {files}
Directories: {dirs}
        """
    except Exception as e:
        return f"Error getting workspace info: {str(e)}"


if __name__ == "__main__":
    print(f"Starting Void Sandboxed Filesystem MCP Server...")
    print(f"Allowed root: {security.allowed_root}")
    print(f"Config file: {security.config_path}")
    
    mcp.run()