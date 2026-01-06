import os
import asyncio
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


async def call_ai_defense_inspection(user_message: str):
    # Endpoint for Chat Inspection (Global/US) - Change to 'eu' or 'ap' subdomain if needed
    url = "https://us.api.inspect.aidefense.security.cisco.com/api/v1/inspect/chat"

    headers = {
        "X-Cisco-AI-Defense-API-Key": "bc05095aedefcdc8feb5290d4455416661dfe7f100f3288a56dcc3443ef724e8",
        "Content-Type": "application/json"
    }

    # Payload matching ChatInspectRequest schema
    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "metadata": {
            "user": "end-user-id", # Optional: Map to actual user ID
            "src_app": "nyasukun-langchain-cicd-1767702252"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Returns InspectResponse (classifications, is_safe, severity, etc.)
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

    # AI Defense Inspection
    try:
        inspection_result = await call_ai_defense_inspection(user_message)
        print(f"AI Defense Inspection: {inspection_result}")

        # Check if the message is safe to proceed
        if not inspection_result.get("is_safe", True):
            print("Warning: Message flagged by AI Defense. Proceeding with caution.")
    except Exception as e:
        print(f"AI Defense inspection error: {e}")

    response = chain.invoke({"input": user_message})

    print(f"User: {user_message}")
    print(f"AI: {response.content}")


if __name__ == "__main__":
    asyncio.run(main())
