"""Claude Code CLI subprocess wrapper with session management."""

import asyncio
import json
import os
from config import CLAUDE_CMD, CLAUDE_TIMEOUT, CLAUDE_WORKING_DIR


class ClaudeInterface:
    """Wraps the Claude Code CLI for non-interactive use."""

    def __init__(self):
        self.session_id: str | None = None

    async def send(self, text: str, working_dir: str | None = None) -> str:
        """Send a prompt to Claude Code and return the response text.

        Uses --resume SESSION_ID for conversation continuity when available.
        """
        cwd = working_dir or CLAUDE_WORKING_DIR or os.getcwd()

        cmd = [CLAUDE_CMD, "-p", text, "--output-format", "json"]

        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        print(f"[Claude] Running: {' '.join(cmd[:6])}...")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=CLAUDE_TIMEOUT,
            )

            output = stdout.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                err = stderr.decode("utf-8", errors="replace").strip()
                print(f"[Claude] Error (exit {proc.returncode}): {err[:200]}")
                return f"Claude encountered an error: {err[:300]}"

            return self._parse_response(output)

        except asyncio.TimeoutError:
            print("[Claude] Timed out")
            return "Claude took too long to respond. Try a simpler request."
        except FileNotFoundError:
            return "Claude Code CLI not found. Make sure 'claude' is installed and on PATH."
        except Exception as e:
            print(f"[Claude] Exception: {e}")
            return f"Error communicating with Claude: {str(e)[:200]}"

    def _parse_response(self, output: str) -> str:
        """Parse JSON output from Claude Code CLI, extract text and session_id."""
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # Not JSON - return as plain text
            return output if output else "Claude returned an empty response."

        # Extract session_id for continuity
        if isinstance(data, dict):
            sid = data.get("session_id")
            if sid:
                self.session_id = sid
                print(f"[Claude] Session: {sid[:12]}...")

            # Extract the result text
            result = data.get("result", "")
            if result:
                return result

            # Try other common fields
            for key in ("text", "content", "message", "output"):
                if key in data and data[key]:
                    return str(data[key])

        return output if output else "Claude returned an empty response."

    def new_session(self):
        """Start a new conversation (forget session_id)."""
        self.session_id = None
        print("[Claude] New session started.")
