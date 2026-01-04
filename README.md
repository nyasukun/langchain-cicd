# LangChain AI Security CI/CD Demo

This project demonstrates how to integrate AI Security into the CI/CD process (GitHub Actions) for a LangChain application. It uses the Claude Agent SDK to analyze the codebase and setup security measures via the Cisco AI Defense MCP (Model Context Protocol).

## Overview

The goal is to automatically ensure AI security practices are followed whenever code is pushed. This is achieved by:

1.  **Codebase Analysis**: Using Claude Agent SDK to scan the code.
2.  **LLM Provider Check**: Identifying LLM provider usage and obtaining the system prompt if available.
3.  **Security Validation**: Invoking the Cisco AI Defense Validation via MCP to validate the system prompt.
4.  **Guardrails Setup**: Identifying chat API calls and configuring Guardrails via MCP.

## Prerequisites

*   Python 3.10+
*   LangChain
*   Claude Agent SDK
*   Cisco AI Defense MCP (`nyasukun/ai-defense-mcp`)
*   OpenAI API Key (for the application)
*   Anthropic API Key (for the Claude Agent SDK)

## Usage

This project is designed to be run as part of a GitHub Actions workflow. However, you can also run the security check script locally using the MCP wrapper.

### Local Execution

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    pip install claude-agent-sdk mcp
    ```

2.  Clone and setup the AI Defense MCP server in the project root:
    ```bash
    git clone https://github.com/nyasukun/ai-defense-mcp.git
    cd ai-defense-mcp
    pip install -r requirements.txt
    cd ..
    ```

3.  Set up environment variables:
    ```bash
    cp .env.example .env
    # Edit .env to include your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, AIC_MANAGEMENT_API_KEY)
    ```

4.  Run the security check:
    ```bash
    python scripts/ai_security_check.py
    ```

## CI/CD Workflow

The `.github/workflows/ai-security.yml` file defines the automation process. It triggers on `push` events and orchestrates the security validation steps using a custom MCP wrapper to communicate with the AI Defense toolset.
