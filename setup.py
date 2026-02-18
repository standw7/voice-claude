"""Setup script for Voice Claude.

Installs dependencies and copies the /voice slash command to ~/.claude/commands/
so it's available globally in Claude Code on any machine.
"""

import os
import shutil
import subprocess
import sys


def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Install dependencies
    print("Installing dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r",
        os.path.join(project_dir, "requirements.txt"),
    ])

    # Copy slash command to ~/.claude/commands/
    claude_commands_dir = os.path.expanduser("~/.claude/commands")
    os.makedirs(claude_commands_dir, exist_ok=True)

    src = os.path.join(project_dir, "commands", "voice.md")
    dst = os.path.join(claude_commands_dir, "voice.md")

    # Update the command with the actual path on this machine
    with open(src, "r") as f:
        content = f.read()

    # Replace the generic path hint with the actual path
    main_py = os.path.join(project_dir, "main.py").replace("\\", "/")
    patched = content.replace(
        "<path-to-voice-claude>/main.py",
        main_py,
    )

    with open(dst, "w") as f:
        f.write(patched)

    print(f"Installed /voice command to {dst}")
    print(f"Voice Claude path: {main_py}")
    print("\nSetup complete! Use /voice in Claude Code to start voice mode.")


if __name__ == "__main__":
    main()
