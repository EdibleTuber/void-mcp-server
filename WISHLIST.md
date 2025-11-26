# MCP Server & Void Integration Wishlist

Feature requests and improvements for future development.

---

## Void Editor Improvements

### MCP Server Health Check UI
**Priority:** High
**Effort:** Medium
**Category:** Void
**Requested:** 2025-11-24

**Problem:** Currently, Void shows green when the MCP server process is running, but there's no way to verify:
- If Void is actually calling `tools/list`
- If the server is returning tools correctly
- If tools are being passed to the LLM
- What errors might be occurring in the communication

**Proposed Solution:**
Add an MCP health check panel in Void that shows:
```
MCP Server: filesystem
Status: Connected ✓
Process ID: 12345
Tools Available: 8
  - read_file ✓
  - write_file ✓
  - create_file ✓
  ...
Last Request: tools/list (2s ago)
Last Response: 200 OK
```

**Bonus Features:**
- Button to manually trigger `tools/list` request
- Show recent MCP requests/responses
- Display server logs/errors
- Test tool execution with sample inputs

**Impact:** Would massively help debugging MCP integration issues

---

## How to Use This File

Add new wishlist items as you think of them. When implementing, move completed items to a CHANGELOG.md file.
