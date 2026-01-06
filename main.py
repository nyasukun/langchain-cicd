import os
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


async def call_ai_defense_inspection(user_message: str):
    """Call AI Defense inspection API to check user input for security threats."""
    url = "https://us.api.inspect.aidefense.security.cisco.com/api/v1/inspect/chat"

    headers = {
        "X-Cisco-AI-Defense-API-Key": "f4f8aad4c1b69d9528b20d1f642e1f0a3cf3c3db757f48335aaefdeee047cbe2",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "metadata": {
            "user": "end-user-id",
            "src_app": "nyasukun-langchain-cicd-1767701931"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
        return

    llm = ChatOpenAI(model="gpt-3.5-turbo")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that translates English to Japanese."),
        ("user", "{input}")
    ])

    chain = prompt | llm

    user_message = "Hello, how are you?"

    # AI Defense: Inspect user input before sending to LLM
    print("Calling AI Defense inspection...")
    inspection_result = await call_ai_defense_inspection(user_message)
    print(f"Inspection result: {inspection_result}")

    # Check if input is safe
    if not inspection_result.get("is_safe", True):
        print(f"AI Defense blocked unsafe input. Severity: {inspection_result.get('severity')}")
        return

    response = chain.invoke({"input": user_message})

    print(f"User: {user_message}")
    print(f"AI: {response.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
