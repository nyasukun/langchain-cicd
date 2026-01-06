import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def main():
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
    response = chain.invoke({"input": user_message})

    print(f"User: {user_message}")
    print(f"AI: {response.content}")


if __name__ == "__main__":
    main()
