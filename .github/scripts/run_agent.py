#!/usr/bin/env python3
"""
AI Security Agent - Orchestrates AI Defense operations.

Receives instructions from AGENT_PROMPT environment variable,
gathers context, and executes appropriate security operations.

Environment Variables:
    AGENT_PROMPT: Instructions for the agent (from workflow)

Architecture:
    workflow (AGENT_PROMPT) → agent → MCP → AI Defense
"""

import argparse
import asyncio
import json
import os
import sys

from claude_code_sdk import query, ClaudeCodeOptions, Message

# Add script directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from lib.git import get_git_context
from lib.mcp import get_mcp_config


# Agent system prompt
SYSTEM_PROMPT = """You are an AI Security Agent. Your role is to analyze codebases for LLM usage and apply AI Defense security measures.

## Your Capabilities

### Analysis
- Find Python files and detect LLM frameworks (LangChain, OpenAI, Anthropic)
- Extract system prompts from the code
- Identify LLM call sites (.invoke, client.chat.completions.create, etc.)

### Validation (via MCP)
- Call `mcp__ai-defense__start_ai_validation` to start a validation scan

### Guardrails (via MCP)
- Call `mcp__ai-defense__setup_ai_defense_guardrails` to register app and get API key
- Modify files to add inspection code
- Create git branch and PR

## Your Workflow
1. Read the user's request carefully
2. Gather context about the codebase (use Glob, Grep, Read)
3. Execute the requested operation using appropriate tools
4. Report results clearly

## Output Format
Provide a structured summary at the end:
```
## Summary
- Repository: {owner}/{repo}
- Operation: {validation/guardrails}
- Status: {success/failure}
- Details: {relevant findings}
```

## Important Rules
- Only analyze/modify code in the working directory (exclude .venv/, .github/)
- Verify syntax after file modifications: `python -m py_compile {file}`
- Handle errors gracefully
- Never use force push or destructive git commands
"""

# All available tools
TOOLS_FULL = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
    "mcp__ai-defense__start_ai_validation",
    "mcp__ai-defense__setup_ai_defense_guardrails",
]

TOOLS_READONLY = [
    "Read",
    "Glob",
    "Grep",
    "Bash",
]


def get_context_summary(working_dir: str, commit_id: str = None) -> str:
    """Get git context as formatted string."""
    try:
        ctx = get_git_context(commit_id=commit_id)
        return f"""## Context
- Repository: {ctx.owner}/{ctx.repo}
- Branch: {ctx.branch}
- Commit: {ctx.short_commit_id}
- Running in CI: {ctx.is_ci}
- Working Directory: {working_dir}
"""
    except Exception as e:
        return f"""## Context
- Working Directory: {working_dir}
- Git context unavailable: {e}
"""


def build_user_prompt(context: str, agent_prompt: str, dry_run: bool) -> str:
    """Build the full user prompt."""
    mode = ""
    if dry_run:
        mode = """
## MODE: DRY RUN
Analyze only. Do NOT:
- Modify any files
- Call MCP tools
- Create branches or PRs
Just report what you would do.
"""
    return f"{context}\n{mode}\n{agent_prompt}"


async def run_agent(
    working_dir: str,
    commit_id: str = None,
    dry_run: bool = False,
    output_file: str = None
) -> dict:
    """Run the agent."""
    agent_prompt = os.environ.get("AGENT_PROMPT")
    if not agent_prompt:
        return {
            "status": "error",
            "error": "AGENT_PROMPT environment variable is required"
        }

    context = get_context_summary(working_dir, commit_id)
    user_prompt = build_user_prompt(context, agent_prompt, dry_run)
    tools = TOOLS_READONLY if dry_run else TOOLS_FULL

    try:
        mcp_servers = get_mcp_config(working_dir)
    except FileNotFoundError as e:
        return {"status": "error", "error": str(e)}

    result = {
        "status": "running",
        "messages": [],
        "final_output": None,
        "pr_url": None
    }

    print("=" * 60)
    print("AI Security Agent")
    print("=" * 60)
    print(context)
    print(f"Dry Run: {dry_run}")
    print("-" * 60)

    try:
        options = ClaudeCodeOptions(
            cwd=working_dir,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=tools,
            permission_mode="default",
            mcp_servers=mcp_servers
        )

        async for message in query(prompt=user_prompt, options=options):
            if isinstance(message, Message):
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            text = block.text
                            print(text)
                            result["messages"].append(text)
                            if "## Summary" in text:
                                result["final_output"] = text
                            if "PR URL:" in text:
                                for line in text.split("\n"):
                                    if "PR URL:" in line:
                                        url = line.split("PR URL:")[-1].strip()
                                        if url.startswith("http"):
                                            result["pr_url"] = url
                elif hasattr(message, 'result'):
                    result["final_output"] = message.result
            else:
                msg_str = str(message)
                print(msg_str)
                result["messages"].append(msg_str)

        result["status"] = "completed"

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        result["status"] = "error"
        result["error"] = str(e)

    if output_file:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResults written to: {output_file}")

    return result


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run AI Security Agent")
    parser.add_argument("--target-dir", default=".", help="Directory to analyze")
    parser.add_argument("--commit-id", help="Explicit commit ID")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only")
    parser.add_argument("--output", help="Output file (JSON)")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)
    os.chdir(target_dir)

    result = await run_agent(
        working_dir=target_dir,
        commit_id=args.commit_id,
        dry_run=args.dry_run,
        output_file=args.output
    )

    print()
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"Status: {result['status']}")
    if result.get("pr_url"):
        print(f"PR URL: {result['pr_url']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
        return 1

    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
