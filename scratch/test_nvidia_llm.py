import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from src.ai.llm_client import llm_chat
from src.core.config import settings

def test_llm():
    print(f"Testing LLM with provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    print(f"Base URL: {settings.llm_base_url}")
    
    try:
        messages = [{"role": "user", "content": "Привет! Ты работаешь?"}]
        response = llm_chat(messages)
        print("\n--- Response ---")
        print(response)
        print("----------------")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_llm()
