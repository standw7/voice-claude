"""MCP permission server for Voice Claude.

This runs as a stdio MCP server process spawned by Claude Code. When Claude
wants to execute a risky tool, this server intercepts the permission request
and communicates with the main Voice Claude process over a localhost TCP socket
to trigger a voice confirmation flow.

Protocol over TCP:
  Main process sends:   CONFIRM:<description>\n
  This server replies:  YES\n  or  NO\n
"""

import sys
import json
import socket
import os

# TCP port for IPC with main Voice Claude process
PERMISSION_PORT = int(os.environ.get("VOICE_CLAUDE_PERMISSION_PORT", "19384"))

# Tools that are always safe to approve
SAFE_TOOLS = {
    "Read", "Glob", "Grep", "Edit", "Write", "NotebookEdit",
    "WebSearch", "WebFetch", "Task", "TodoRead", "TodoWrite",
}

# Bash commands that are safe to auto-approve
SAFE_BASH_PATTERNS = [
    "git status", "git log", "git diff", "git branch",
    "ls ", "pwd", "echo ", "cat ", "head ", "tail ",
    "python -c", "node -e", "npm list", "pip list",
    "which ", "where ", "type ",
]


def is_safe_tool(tool_name: str, tool_input: dict) -> bool:
    """Check if a tool invocation is safe to auto-approve."""
    if tool_name in SAFE_TOOLS:
        return True

    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return any(cmd.strip().startswith(p) for p in SAFE_BASH_PATTERNS)

    return False


def ask_voice_confirmation(description: str) -> bool:
    """Ask the main process for voice confirmation over TCP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(60)  # 60s timeout for user to respond
            sock.connect(("127.0.0.1", PERMISSION_PORT))
            sock.sendall(f"CONFIRM:{description}\n".encode())
            response = sock.recv(1024).decode().strip()
            return response.upper() == "YES"
    except Exception as e:
        print(f"[PermissionServer] TCP error: {e}", file=sys.stderr)
        # Default to deny on connection failure
        return False


def handle_mcp_request(request: dict) -> dict:
    """Process an MCP JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {
                    "name": "voice-claude-permissions",
                    "version": "1.0.0",
                },
            },
        }

    if method == "notifications/initialized":
        return None  # No response needed for notifications

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "check_permission",
                        "description": "Check if a tool invocation should be allowed",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "tool_name": {"type": "string"},
                                "tool_input": {"type": "object"},
                                "description": {"type": "string"},
                            },
                            "required": ["tool_name", "description"],
                        },
                    }
                ],
            },
        }

    if method == "tools/call":
        tool_name = params.get("arguments", {}).get("tool_name", "")
        tool_input = params.get("arguments", {}).get("tool_input", {})
        description = params.get("arguments", {}).get("description", "")

        if is_safe_tool(tool_name, tool_input):
            allowed = True
        else:
            allowed = ask_voice_confirmation(
                f"{tool_name}: {description}"
            )

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"allowed": allowed}),
                    }
                ],
            },
        }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }


def main():
    """MCP stdio server main loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = handle_mcp_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
