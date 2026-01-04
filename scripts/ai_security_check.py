import asyncio
import os
import sys
from claude_agent_sdk import query, ClaudeAgentOptions

# This script assumes that 'nyasukun/ai-defense-mcp' provides tools for 'validate_system_prompt' and 'setup_guardrails'.
# We use a CLI wrapper to invoke these tools via the agent's Bash tool.

async def main():
    print("Starting AI Security Check...")
    
    # Define the goal for the agent
    prompt = """
    You are an AI Security Engineer. Your task is to analyze the codebase and enforce security measures.
    You have permission to EDIT the code to fix security issues.
    
    Step 1: Analyze the codebase (e.g., using 'ls' and 'cat') to find where the LLM Provider (like OpenAI, Anthropic, etc.) is initialized.
    If you find it, check if a 'system prompt' is defined.
    
    If a system prompt is found, you MUST validate it using the 'validate_system_prompt' tool from the AI Defense MCP.
    Since you cannot call MCP tools directly, you MUST use the 'mcp_wrapper.py' script via the 'Bash' tool.
    
    Command to run:
    python scripts/mcp_wrapper.py --tool validate_system_prompt --args '{"system_prompt": "YOUR_FOUND_PROMPT"}'
    
    Step 2: Analyze the application to find where the LLM Chat API is called (e.g., `invoke`, `chat`, `call`).
    If found, use the 'setup_ai_defense_guardrails' tool from the AI Defense MCP to configure guardrails for that interaction.
    
    Command to run:
    python scripts/mcp_wrapper.py --tool setup_ai_defense_guardrails --args '{"application_name": "langchain-app", "description": "LangChain Chat Application"}'
    
    Step 3: IMPLEMENT THE FIXES.
    If the 'setup_ai_defense_guardrails' tool provides code snippets or instructions, you MUST EDIT the application code (using the 'Edit' tool) to integrate these guardrails. 
    Wrap the LLM call with the suggested guardrail logic.
    
    Report your findings and confirm the changes you made.
    """
    
    try:
        async for message in query(
            prompt=prompt,
            # We explicitly allow Bash to run the wrapper. Read/Glob/Grep/Edit are standard.
            options=ClaudeAgentOptions(
                allowed_tools=["Bash", "Read", "Glob", "Grep", "Edit"] 
            )
        ):
            print(message)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
