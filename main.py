import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables (expecting OPENAI_API_KEY)
load_dotenv()

def main():
    # Check if API key is present
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found. Please set it in .env or environment variables.")
        return

    # Initialize the ChatOpenAI model
    llm = ChatOpenAI(model="gpt-3.5-turbo")

    # Define the prompt template with system and user messages
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that translates English to Japanese."),
        ("user", "{input}")
    ])

    # Create a chain combining the prompt and the LLM
    chain = prompt | llm

    # Fixed user message to send
    user_message = "Hello, how are you?"

    # Invoke the chain
    response = chain.invoke({"input": user_message})

    # Print the response content
    print(f"User: {user_message}")
    print(f"AI: {response.content}")

if __name__ == "__main__":
    main()
