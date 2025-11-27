# Caching & Optimization Explained

## What is Caching/Optimization?

### Simple Approach (What we'll start with)
- Read file from disk every time
- Parse/process on demand
- No memory storage between operations
- **Pros**: Simple, no bugs, low memory
- **Cons**: Slower for repeated operations

### Cached/Optimized Approach
- Store parsed data in memory
- Reuse previous computations
- Build indexes for fast lookup
- **Pros**: Much faster
- **Cons**: More complex, uses RAM, cache invalidation bugs

---

## Specific Optimization Examples

### 1. File Content Caching
**Without Cache**:
```python
def read_file(path):
    with open(path) as f:
        return f.read()  # Reads from disk every time
```

**With Cache**:
```python
file_cache = {}  # In-memory cache

def read_file(path):
    if path in file_cache:
        return file_cache[path]  # Return from memory

    with open(path) as f:
        content = f.read()
        file_cache[path] = content  # Store for next time
        return content
```

**Challenge**: What if file changes on disk? Cache is stale.

---

### 2. AST Parsing Cache
**Without Cache** (simple):
```python
def find_function(function_name, file_path):
    with open(file_path) as f:
        tree = ast.parse(f.read())  # Parse every time - SLOW
        # Search tree for function...
```

**With Cache**:
```python
ast_cache = {}

def find_function(function_name, file_path):
    if file_path not in ast_cache:
        with open(file_path) as f:
            ast_cache[file_path] = ast.parse(f.read())  # Parse once

    tree = ast_cache[file_path]  # Reuse parsed tree - FAST
    # Search tree...
```

**Impact**:
- Parsing a file: ~50ms
- Searching cached AST: ~1ms
- 50x speedup!

---

### 3. Symbol Index (Advanced)
**Without Index** (simple search):
```python
def find_symbol(symbol_name):
    results = []
    for file in all_python_files:
        tree = ast.parse(read_file(file))
        # Walk entire tree looking for symbol
        for node in ast.walk(tree):
            if matches(node, symbol_name):
                results.append(node)
    return results  # Searches EVERY file, EVERY time
```

**With Index**:
```python
# Build index once
symbol_index = {
    "User": [("models/user.py", 15), ("views/user.py", 8)],
    "authenticate": [("auth.py", 42), ("utils.py", 103)]
}

def find_symbol(symbol_name):
    return symbol_index.get(symbol_name, [])  # O(1) lookup
```

**Impact**:
- Without index: Search 100 files = 5 seconds
- With index: Lookup = 0.001 seconds
- 5000x speedup!

**Challenge**: Index must be rebuilt when files change

---

## When Do We Need Optimization?

### Start Simple (Our Approach)
For personal projects (< 1000 files):
- ✅ No caching needed
- ✅ Parse on demand
- ✅ Simple code, no bugs
- ⚠️ Slight delay on operations (< 1 second)

### Add Caching Later
When you notice:
- Operations taking > 2 seconds
- Doing same operation repeatedly
- Working with large codebases (> 10,000 files)

---

## Recommendation for Phase 1

**Don't optimize yet.** Here's why:

1. **Premature optimization is root of all evil**
   - Adds complexity
   - More bugs
   - Harder to debug

2. **Personal projects are small**
   - Your projects likely < 100 Python files
   - Modern SSD can read 100 files in < 100ms
   - Not worth the complexity

3. **Add when needed**
   - Profile first: measure what's actually slow
   - Then optimize the bottleneck
   - Don't guess what needs optimization

---

## When to Add Optimization

### Phase 1 (Now): Keep it Simple
```python
@mcp.tool()
def edit_file(path: str, old_text: str, new_text: str) -> str:
    # Read file
    content = read_file(path)

    # Simple replace
    if old_text not in content:
        return "Error: old_text not found"

    new_content = content.replace(old_text, new_text)

    # Write file
    write_file(path, new_content)
    return "Success"
```

Simple, clear, works great for 99% of use cases.

### Phase 2 (Later): Add Cache if Slow
```python
# Only if we measure slowness and identify this as bottleneck
from functools import lru_cache

@lru_cache(maxsize=100)
def read_file_cached(path: str, mtime: float) -> str:
    # mtime = modification time, invalidates cache when file changes
    return read_file(path)
```

Only add when we have proof it's needed.

---

## Summary

**For Edit File Tool (Phase 1)**:
- ❌ No caching
- ❌ No indexes
- ❌ No optimization
- ✅ Simple, correct, maintainable code

**For Symbol Search (Future)**:
- ⚠️ Consider caching parsed ASTs
- ⚠️ Only if profiling shows it's slow
- ✅ Start simple, measure, then optimize

**Philosophy**:
> Make it work, make it right, make it fast - in that order.

We're at "make it work" stage. Optimization is "make it fast" - we'll do that later if needed.
