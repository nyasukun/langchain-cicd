# LangChain AI Security CI/CD Demo

This repository demonstrates how to integrate AI Security into your CI/CD pipeline for LangChain applications.

---

# LangChain Demo

A simple English-to-Japanese translation chatbot. This application serves as the target for the AI Security CI/CD pipeline.

## Application Overview

```python
# main.py
llm = ChatOpenAI(model="gpt-3.5-turbo")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that translates English to Japanese."),
    ("user", "{input}")
])

chain = prompt | llm
response = chain.invoke({"input": user_message})
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set OPENAI_API_KEY in .env

# Run
python main.py
```

---

# AI Security CI/CD Demo

Automates AI application security checks using Claude Agent SDK and Cisco AI Defense MCP.

## Architecture

```
workflow (AGENT_PROMPT) → Agent (Claude Agent SDK) → MCP → Cisco AI Defense
```

The workflow provides instructions to the agent, which then calls AI Defense APIs via MCP.

## Features

| Feature | Description |
|---------|-------------|
| **Validation** | Analyzes LLM usage patterns and checks system prompts for vulnerabilities |
| **Guardrails** | Inserts runtime inspection code at LLM call sites and creates a PR |

> **Note:** The Guardrails agent may hardcode API keys in generated branches. Delete these branches after testing and rotate API keys if needed.

## File Structure

```
.github/
├── workflows/
│   └── ai-security.yml       # Workflow definition + agent instructions
├── scripts/
│   ├── run_agent.py          # Agent execution script
│   └── lib/
│       ├── git.py            # Git context utilities
│       └── mcp.py            # MCP server configuration
├── requirements.txt          # CI/CD dependencies
└── ai-defense-mcp/           # Cloned during CI/CD execution
```

## Workflow Explained

### Triggers

- `push` / `pull_request` to main: Automatic execution
- `workflow_dispatch`: Manual execution with options

### Defining Agent Instructions

Agent instructions are defined in the workflow's `env` section:

```yaml
env:
  VALIDATION_AGENT_PROMPT: |
    Analyze this codebase for LLM usage patterns and run AI Defense validation.
    ## Your Task
    1. Find all Python files (exclude .venv/, __pycache__/, .github/)
    2. Detect LLM frameworks: LangChain, OpenAI SDK, Anthropic SDK
    ...

  GUARDRAILS_AGENT_PROMPT: |
    Apply AI Defense runtime guardrails to this codebase and create a PR.
    ## Your Task
    1. Find LLM call sites: .invoke(), client.chat.completions.create()
    ...
```

### Job Execution

The agent receives instructions via the `AGENT_PROMPT` environment variable and executes autonomously:

```yaml
- name: Run Agent
  env:
    AGENT_PROMPT: ${{ env.VALIDATION_AGENT_PROMPT }}
  run: python .github/scripts/run_agent.py --output report.json
```

## Adding to Your Repository

### 1. Copy Required Files

```bash
# Copy the .github directory
cp -r .github/workflows/ai-security.yml your-repo/.github/workflows/
cp -r .github/scripts your-repo/.github/
cp .github/requirements.txt your-repo/.github/
```

### 2. Configure GitHub Secrets

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | For Claude Agent SDK |
| `OPENAI_API_KEY` | For OpenAI models (optional) |
| `AIC_MANAGEMENT_API_KEY` | Cisco AI Defense Management API |

### 3. Customize the Workflow

Edit `VALIDATION_AGENT_PROMPT` / `GUARDRAILS_AGENT_PROMPT` in `ai-security.yml` to adjust agent behavior.

## Local Testing

### Environment Setup

```bash
# Install CI/CD dependencies
pip install -r .github/requirements.txt

# Clone AI Defense MCP
git clone --depth 1 https://github.com/nyasukun/ai-defense-mcp.git .github/ai-defense-mcp
pip install -r .github/ai-defense-mcp/requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export AIC_MANAGEMENT_API_KEY="your-key"
```

### Running Validation Agent

```bash
export AGENT_PROMPT="
Analyze this codebase for LLM usage patterns.
Find Python files, detect LLM frameworks, and report findings.
"

# Dry-run (analysis only, no API calls)
python .github/scripts/run_agent.py --dry-run

# Full execution
python .github/scripts/run_agent.py --output validation-report.json
```

### Running Guardrails Agent

```bash
export AGENT_PROMPT="
Apply AI Defense runtime guardrails to this codebase.
Find LLM call sites and report what changes would be made.
"

# Dry-run (analysis only, no file modifications)
python .github/scripts/run_agent.py --dry-run

# Full execution (modifies files, creates PR)
export GITHUB_TOKEN="your-token"
python .github/scripts/run_agent.py --output guardrails-report.json
```

### Options

| Option | Description |
|--------|-------------|
| `--target-dir` | Directory to analyze (default: current) |
| `--commit-id` | Commit ID (auto-detected) |
| `--dry-run` | Analysis only, no modifications |
| `--output` | Output report file (JSON) |

## Supported Frameworks

- **LangChain** (`langchain_openai`, `langchain_anthropic`)
- **OpenAI SDK** (`openai`)
- **Anthropic SDK** (`anthropic`)

## References

- [Claude Agent SDK](https://docs.anthropic.com/)
- [Cisco AI Defense](https://www.cisco.com/site/us/en/products/security/ai-defense/index.html)
- [AI Defense MCP](https://github.com/nyasukun/ai-defense-mcp)
