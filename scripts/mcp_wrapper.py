import argparse
import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# This script acts as a bridge to run specific tools on the AI Defense MCP server.
# It uses the 'mcp' python package to communicate via stdio.

async def run_tool(tool_name, tool_args):
    # We assume ai-defense-mcp is located relative to this script or in a knowing location.
    # In CI/CD, we will unpack it in a specific folder. 
    # Let's assume it is in "ai-defense-mcp" directory in the root of the workspace.
    
    server_dir = os.path.abspath(os.path.join(os.getcwd(), "ai-defense-mcp"))
    if not os.path.exists(server_dir):
        # Fallback for local testing if needed, or error out
        print(f"Error: AI Defense MCP directory not found at {server_dir}", file=sys.stderr)
        sys.exit(1)

    # Detect the python interpreter to use for the server
    # Ideally it should use its own venv, but for CI simplification we might use the same environment
    # if dependencies are installed there.
    # Let's try to find the venv python if it exists, otherwise use system python.
    venv_python = os.path.join(server_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        server_python = venv_python
    else:
        server_python = sys.executable

    server_params = StdioServerParameters(
        command=server_python,
        args=["-m", "src.server"],
        cwd=server_dir,
        env={**os.environ} # Pass current env vars (including API keys)
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools to verify (optional, but good for debug)
            # tools = await session.list_tools()
            # print(f"Available tools: {[t.name for t in tools.tools]}", file=sys.stderr)
            
            try:
                result = await session.call_tool(tool_name, arguments=tool_args)
                print(json.dumps(result.content, default=str)) # Dump result as JSON string for easy parsing by Agent
            except Exception as e:
                print(f"Error calling tool {tool_name}: {e}", file=sys.stderr)
                sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run MCP tool")
    parser.add_argument("--tool", required=True, help="Name of the tool to run")
    parser.add_argument("--args", required=True, help="JSON string of arguments for the tool")
    
    args = parser.parse_args()
    
    try:
        tool_args = json.loads(args.args)
    except json.JSONDecodeError:
        print("Error: --args must be a valid JSON string", file=sys.stderr)
        sys.exit(1)
        
    asyncio.run(run_tool(args.tool, tool_args))

if __name__ == "__main__":
    main()
