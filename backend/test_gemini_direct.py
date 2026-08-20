import asyncio
import os
from app.engine.providers.gemini_provider import GeminiProvider
from app.config.settings import settings

async def main():
    print(f"Testing model: {settings.GEMINI_MODEL}")
    provider = GeminiProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
    
    code = "def is_even(n):\n    return n % 2 == 0\n"
    print("Sending code to GeminiProvider...")
    result = await provider.review_code(code, "Python")
    
    print("\n--- RESULT ---")
    print(f"Status: {result.status}")
    print(f"Error: {result.error_message}")
    if result.status == "success":
        print(f"Improved code length: {len(result.improved_code) if result.improved_code else 0}")
        print(f"Issues found: {len(result.issues)}")
        print(f"Usage input: {result.usage['prompt_tokens']}")
        print(f"Usage output: {result.usage['candidates_tokens']}")
        print(f"Usage total: {result.usage['total_tokens']}")
    
if __name__ == "__main__":
    asyncio.run(main())
