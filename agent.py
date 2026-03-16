from browser_use.llm.google.chat import ChatGoogle


def create_llm(api_key: str) -> ChatGoogle:
    return ChatGoogle(
        model="gemini-2.5-flash",
        api_key=api_key,
        temperature=0.1,
    )
