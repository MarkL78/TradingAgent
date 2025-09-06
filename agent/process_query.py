import requests
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"),)

def call_claude(prompt: str, model="claude-sonnet-4-20250514", max_tokens=1024) -> str:
    """
    Call Claude API with a given prompt.

    Args:
        prompt (str): Input text to send to Claude.
        model (str): Claude model name.
        max_tokens (int): Maximum tokens to generate.

    Returns:
        str: Claude's response text.
    """

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": "Hello, Claude"}])
    
    print(message)