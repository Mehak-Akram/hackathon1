import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def test_gemini_api():
    # Test the current configuration
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        print("GEMINI_API_KEY not found in environment")
        return

    print("Testing Gemini API connection...")

    # Current configuration from the code
    client = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    try:
        response = await client.chat.completions.create(
            model="gemini-2.0-flash",  # Current model
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("Success with gemini-2.0-flash!")
        print(f"Response: {response.choices[0].message.content[:50]}...")
    except Exception as e:
        print(f"Error with gemini-2.0-flash: {e}")

        # Try with gemini-pro or gemini-1.5-flash
        try:
            response = await client.chat.completions.create(
                model="gemini-1.5-flash",  # Alternative model
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print("Success with gemini-1.5-flash!")
            print(f"Response: {response.choices[0].message.content[:50]}...")
        except Exception as e2:
            print(f"Error with gemini-1.5-flash: {e2}")

            # Try with gemini-pro
            try:
                response = await client.chat.completions.create(
                    model="gemini-pro",  # Alternative model
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                print("Success with gemini-pro!")
                print(f"Response: {response.choices[0].message.content[:50]}...")
            except Exception as e3:
                print(f"Error with gemini-pro: {e3}")
                print("All model attempts failed")

if __name__ == "__main__":
    asyncio.run(test_gemini_api())