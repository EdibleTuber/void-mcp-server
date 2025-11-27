# Agentic Code Assistant Improvements Plan

## Current State Analysis

### What We Have ✅
1. **Basic Filesystem Operations** (8 tools)
   - Read, write, create, delete files
   - List, create directories
   - Move/rename files
   - Search in files (basic grep)

2. **Security Layer**
   - Path sandboxing
   - Extension whitelisting
   - Pattern blocking
   - Size limits

3. **MCP Protocol Integration**
   - Tool annotations (readOnly, destructive, idempotent hints)
   - Resources (security config, workspace info)
   - FastMCP framework

### What's Missing for Agentic Coding 🎯

Comparing to Claude Code (you), here's what would make this more capable:

## Gap Analysis: Current vs. Agentic Assistant

| Capability | Current Server | Claude Code | Priority |
|------------|---------------|-------------|----------|
| **Code Understanding** | ❌ None | ✅ AST parsing, semantic analysis | HIGH |
| **Multi-file Edits** | ❌ One file at a time | ✅ Atomic multi-file operations | HIGH |
| **Partial File Edits** | ❌ Full file replacement | ✅ Precise line-based edits | HIGH |
| **Code Search** | ⚠️ Basic grep | ✅ Semantic search, symbol lookup | MEDIUM |
| **Execution** | ❌ No code execution | ✅ Run tests, scripts, commands | HIGH |
| **Git Integration** | ❌ None | ✅ Full git operations | MEDIUM |
| **Dependency Mgmt** | ❌ None | ✅ Install packages, check deps | MEDIUM |
| **Error Recovery** | ❌ None | ✅ Rollback, undo operations | LOW |
| **Context Aware** | ❌ Stateless | ✅ Maintains conversation context | MEDIUM |

---

## Proposed Improvements

### Phase 1: Enhanced File Operations (HIGH PRIORITY)

#### 1.1 Partial File Editing Tool
**Problem**: Current `write_file` requires full file replacement. For large files, this is inefficient and error-prone.

**Solution**: Add `edit_file` tool with line-based editing:
```python
@mcp.tool()
def edit_file(path: str, old_text: str, new_text: str, replace_all: bool = False) -> str:
    """
    Replace specific text in a file without rewriting entire content.

    Args:
        path: File to edit
        old_text: Exact text to find and replace
        new_text: Replacement text
        replace_all: If True, replace all occurrences. If False, must be unique.
    """
```

**Benefits**:
- Reduces token usage (don't send full file content)
- Safer (only modifies specific sections)
- More precise edits
- Less prone to errors from LLM hallucinations

#### 1.2 Multi-File Operations
**Problem**: Can't atomically modify multiple files (like refactoring a function used in many places)

**Solution**: Add batch operation support:
```python
@mcp.tool()
def batch_edit_files(operations: list[dict]) -> str:
    """
    Atomically perform multiple file operations.
    Rolls back all changes if any operation fails.

    Args:
        operations: List of {action, path, params} dicts
    """
```

**Use Cases**:
- Rename function across multiple files
- Refactor imports
- Update configuration in multiple places

#### 1.3 Read File with Line Numbers
**Problem**: Current `read_file` returns plain content. For editing, we need line context.

**Solution**: Add option to return with line numbers:
```python
@mcp.tool()
def read_file_with_lines(path: str, start_line: int = None, end_line: int = None) -> str:
    """
    Read file with line numbers, optionally reading only a range.
    Returns: "1: line content\n2: line content\n..."
    """
```

---

### Phase 2: Code Execution (HIGH PRIORITY)

#### 2.1 Run Shell Commands
**Problem**: Can't execute tests, run linters, or check build status

**Solution**: Add safe command execution:
```python
@mcp.tool()
def run_command(command: str, cwd: str = ".", timeout: int = 30) -> str:
    """
    Execute a shell command in the workspace.

    Args:
        command: Shell command to run
        cwd: Working directory
        timeout: Max execution time in seconds

    Returns: {"stdout": "...", "stderr": "...", "exit_code": 0}
    """
```

**Security**:
- Command whitelist (only allow npm, pytest, git, etc.)
- Timeout enforcement
- No shell injection (use subprocess with args list)
- Sandboxed environment

**Use Cases**:
- Run tests: `run_command("pytest tests/")`
- Install deps: `run_command("pip install requests")`
- Build: `run_command("npm run build")`
- Lint: `run_command("eslint src/")`

#### 2.2 Background Task Execution
**Problem**: Long-running tasks block the agent

**Solution**: Add async execution with status checking:
```python
@mcp.tool()
def run_command_async(command: str) -> str:
    """Start command in background, return task_id"""

@mcp.tool()
def check_task_status(task_id: str) -> str:
    """Check if background task is complete"""

@mcp.tool()
def get_task_output(task_id: str) -> str:
    """Get output of completed task"""
```

---

### Phase 3: Code Understanding (MEDIUM PRIORITY)

#### 3.1 Symbol Search
**Problem**: Grep search is dumb - can't find where a function is defined or used

**Solution**: Add AST-based symbol search:
```python
@mcp.tool()
def find_symbol(symbol_name: str, symbol_type: str = "any") -> str:
    """
    Find definitions and usages of symbols (functions, classes, variables).

    Args:
        symbol_name: Name to search for
        symbol_type: "function", "class", "variable", or "any"

    Returns: List of locations with context
    """
```

**Implementation**:
- Use Python's `ast` module for .py files
- Use tree-sitter for other languages
- Cache AST parses for performance

#### 3.2 Code Structure Analysis
**Problem**: No way to understand project structure

**Solution**: Add codebase analysis:
```python
@mcp.tool()
def analyze_codebase(directory: str = ".") -> str:
    """
    Analyze codebase structure.
    Returns: {
        "languages": {"python": 45, "js": 30},
        "entry_points": ["main.py", "app.js"],
        "dependencies": ["requests", "flask"],
        "test_files": ["test_*.py"],
        "config_files": ["setup.py", "package.json"]
    }
    """
```

#### 3.3 Show Function/Class Definition
**Problem**: Need to read entire file to see one function

**Solution**:
```python
@mcp.tool()
def get_definition(symbol_name: str, file_path: str = None) -> str:
    """
    Extract just the definition of a function/class.
    If file_path not provided, searches entire codebase.
    """
```

---

### Phase 4: Git Integration (MEDIUM PRIORITY)

#### 4.1 Git Status & Diff
```python
@mcp.tool()
def git_status() -> str:
    """Show current git status"""

@mcp.tool()
def git_diff(file_path: str = None) -> str:
    """Show diff for file or entire repo"""
```

#### 4.2 Git Commit
```python
@mcp.tool()
def git_commit(message: str, files: list[str] = None) -> str:
    """
    Create a git commit.
    If files not provided, commits all staged changes.
    """
```

#### 4.3 Git Branch Operations
```python
@mcp.tool()
def git_create_branch(branch_name: str) -> str:
    """Create and switch to new branch"""

@mcp.tool()
def git_switch_branch(branch_name: str) -> str:
    """Switch to existing branch"""
```

---

### Phase 5: Dependency Management (MEDIUM PRIORITY)

#### 5.1 Package Installation
```python
@mcp.tool()
def install_package(package_name: str, package_manager: str = "auto") -> str:
    """
    Install a package using appropriate package manager.
    Auto-detects: pip, npm, cargo, go get, etc.
    """
```

#### 5.2 Dependency Analysis
```python
@mcp.tool()
def list_dependencies() -> str:
    """
    List all project dependencies.
    Reads from: requirements.txt, package.json, Cargo.toml, etc.
    """

@mcp.tool()
def check_outdated_deps() -> str:
    """Check for outdated dependencies"""
```

---

### Phase 6: Advanced Features (LOW PRIORITY)

#### 6.1 File Watching
```python
@mcp.tool()
def watch_file(path: str, callback: str) -> str:
    """Watch file for changes and trigger callback"""
```

#### 6.2 Undo/Redo
```python
@mcp.tool()
def undo_last_operation() -> str:
    """Rollback the last file operation"""

@mcp.tool()
def show_operation_history() -> str:
    """Show history of file operations"""
```

#### 6.3 Template Generation
```python
@mcp.tool()
def create_from_template(template_name: str, output_path: str, variables: dict) -> str:
    """
    Create files from templates.
    E.g., create_from_template("python_class", "models/user.py", {"name": "User"})
    """
```

---

## Implementation Priority

### Immediate (Week 1-2)
1. **Edit File Tool** - Most impactful for day-to-day coding
2. **Run Command** - Essential for testing/building
3. **Read File with Line Numbers** - Needed for precise edits

### Short Term (Week 3-4)
4. **Git Status/Diff** - Critical for real workflow
5. **Symbol Search** - Better than grep for code navigation
6. **Batch Edit** - For refactoring workflows

### Medium Term (Month 2)
7. **Background Tasks** - For long-running operations
8. **Codebase Analysis** - Project understanding
9. **Git Commit** - Complete git workflow

### Long Term (Month 3+)
10. **Package Management** - Convenience feature
11. **Undo/Redo** - Safety net
12. **Templates** - Nice to have

---

## Technical Considerations

### Performance
- **AST Parsing**: Cache parsed ASTs, use lazy loading
- **Large Files**: Stream content, don't load entire file in memory
- **Search**: Index files for faster search (use SQLite FTS)

### Security
- **Command Execution**: Whitelist commands, no arbitrary shell access
- **Resource Limits**: CPU/memory caps for executed processes
- **Timeout**: All operations have max execution time
- **Sandboxing**: Consider Docker/VM for command execution

### Error Handling
- **Atomic Operations**: Batch edits must all succeed or all fail
- **Validation**: Check file syntax before writing (for known file types)
- **Backup**: Keep backup of original file before edit
- **Clear Errors**: Return actionable error messages

### Compatibility
- **Language Support**: Start with Python, add JS/TS, then others
- **Tool Detection**: Auto-detect which tools are available (git, npm, etc.)
- **Cross-Platform**: Handle Windows/Linux/Mac path differences

---

## Comparison to Alternatives

### vs. Claude Code (this instance)
- **Advantages**: Self-hosted, offline, customizable
- **Disadvantages**: No access to Anthropic infrastructure, smaller context

### vs. GitHub Copilot
- **Advantages**: Full file system access, can run commands
- **Disadvantages**: No inline suggestions, requires explicit prompts

### vs. Cline/Aider
- **Advantages**: MCP protocol (more compatible), cleaner architecture
- **Disadvantages**: Currently fewer features

---

## Next Steps

1. **Review this plan** - Discuss priorities and scope
2. **Prototype Edit Tool** - Start with most valuable feature
3. **Add Tests** - Create test suite for new tools
4. **Update Docs** - Document new capabilities
5. **Benchmark** - Measure performance impact

### Questions to Answer:
1. Which Phase 1 feature should we implement first?
2. Do we want command execution? (Security implications)
3. Should we support multiple languages or focus on Python?
4. What's the target use case: personal projects or team workflows?
5. Performance vs. simplicity: how much caching/optimization needed?

---

## Success Metrics

After improvements, the assistant should be able to:
- ✅ Refactor a function across 10+ files
- ✅ Run tests and fix failures iteratively
- ✅ Add a new feature with proper git workflow
- ✅ Install dependencies and update configs
- ✅ Navigate unfamiliar codebase via symbol search
- ✅ Make surgical edits without full file rewrites

**Target**: Handle 80% of coding tasks that currently require Claude Code or Cursor.
