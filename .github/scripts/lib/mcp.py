"""MCP server configuration for Claude Agent SDK."""

import os
import sys
from typing import Dict, Any


def get_mcp_config(base_dir: str = None) -> Dict[str, Any]:
    """
    Get MCP server configuration for ai-defense-mcp.

    This configuration is used with ClaudeCodeOptions.mcp_servers
    to enable the agent to call AI Defense tools via MCP.

    Tool naming convention:
        mcp__{server_name}__{tool_name}

        Available tools:
        - mcp__ai-defense__start_ai_validation
        - mcp__ai-defense__get_ai_validation_status
        - mcp__ai-defense__setup_ai_defense_guardrails
        - mcp__ai-defense__get_ai_defense_events
        - mcp__ai-defense__get_ai_defense_event_details
    """
    if base_dir is None:
        base_dir = os.getcwd()

    # AI Defense MCP is cloned to .github/ai-defense-mcp during CI/CD
    server_dir = os.path.abspath(os.path.join(base_dir, ".github", "ai-defense-mcp"))

    if not os.path.exists(server_dir):
        raise FileNotFoundError(
            f"AI Defense MCP not found at {server_dir}. "
            "Run: git clone https://github.com/nyasukun/ai-defense-mcp.git .github/ai-defense-mcp"
        )

    # Detect python executable
    venv_python = os.path.join(server_dir, ".venv", "bin", "python")
    project_venv = os.path.join(base_dir, ".venv", "bin", "python")

    if os.path.exists(venv_python):
        server_python = venv_python
    elif os.path.exists(project_venv):
        server_python = project_venv
    else:
        server_python = sys.executable

    return {
        "ai-defense": {
            "command": server_python,
            "args": ["-m", "src.server"],
            "env": {**os.environ, "PYTHONPATH": server_dir},
            "cwd": server_dir
        }
    }
