# backend/phase3_classifier/groq_client.py
# Groq API client — handles all communication with Groq
# Used by Phase 3 (classifier) and Phase 5 (reporter)
# Free tier: plenty of requests for student project

import os
import sys
from groq import Groq
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env from backend/ folder
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


# ─────────────────────────────────────────
# MODEL CONFIG
# ─────────────────────────────────────────

# Best free models on Groq — verify current availability at console.groq.com
# llama-3.3-70b-versatile = best quality, still fast
# llama3-8b-8192 = fastest, good for classification
CLASSIFIER_MODEL = "openai/gpt-oss-120b"
REPORTER_MODEL   = "openai/gpt-oss-120b"

MAX_TOKENS_CLASSIFIER = 500    # Classification needs short focused output
MAX_TOKENS_REPORTER   = 2000   # Reports need longer output

# Global client instance
_client = None


def get_groq_client() -> Groq:
    """
    Get or create Groq client instance.
    Validates API key on first call.

    Returns:
        Groq client instance
    """
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "❌ GROQ_API_KEY not found in .env file.\n"
            "   Get your free key at: https://console.groq.com\n"
            "   Add to .env: GROQ_API_KEY=your_key_here"
        )

    _client = Groq(api_key=api_key)
    print("✅ Groq client initialized")
    return _client


def call_groq(
    prompt: str,
    system_prompt: str = None,
    model: str = None,
    max_tokens: int = None,
    temperature: float = 0.1,
) -> str:
    """
    Make a single call to Groq API.
    Returns the response text string.

    Args:
        prompt: User prompt to send
        system_prompt: Optional system prompt
        model: Model to use (defaults to CLASSIFIER_MODEL)
        max_tokens: Max tokens in response
        temperature: 0.1 = focused/deterministic, 1.0 = creative

    Returns:
        Response text from Groq
    """
    client = get_groq_client()
    model = model or CLASSIFIER_MODEL
    max_tokens = max_tokens or MAX_TOKENS_CLASSIFIER

    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        result = response.choices[0].message.content.strip()
        return result

    except Exception as e:
        error_msg = str(e)

        # Handle common errors clearly
        if "rate_limit" in error_msg.lower():
            print("⚠️  Groq rate limit hit — waiting before retry")
            import time
            time.sleep(10)
            # Retry once
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception as retry_error:
                print(f"❌ Groq retry failed: {retry_error}")
                return ""

        elif "model_not_found" in error_msg.lower():
            print(f"❌ Model '{model}' not available — check console.groq.com")
            return ""

        else:
            print(f"❌ Groq API error: {e}")
            return ""


def call_groq_reporter(prompt: str, system_prompt: str = None) -> str:
    """
    Groq call specifically for report generation.
    Uses higher token limit and slightly higher temperature
    for more natural writing.

    Args:
        prompt: Report generation prompt
        system_prompt: Optional system prompt

    Returns:
        Generated report text
    """
    return call_groq(
        prompt=prompt,
        system_prompt=system_prompt,
        model=REPORTER_MODEL,
        max_tokens=MAX_TOKENS_REPORTER,
        temperature=0.3,   # Slightly more creative for report writing
    )


def test_groq_connection() -> bool:
    """
    Test that Groq API is working correctly.
    Returns True if connection successful, False otherwise.
    """
    try:
        response = call_groq(
            prompt="Reply with exactly: CONNECTION OK",
            system_prompt="You are a test assistant. Follow instructions exactly.",
            max_tokens=20,
        )
        success = "CONNECTION OK" in response.upper()
        if success:
            print("✅ Groq API connection test passed")
        else:
            print(f"⚠️  Groq responded but unexpected output: {response}")
        return success
    except Exception as e:
        print(f"❌ Groq connection test failed: {e}")
        return False


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("🧪 Testing Groq client...\n")

    # Test 1 — connection
    print("=== TEST 1 — Connection ===")
    success = test_groq_connection()

    if not success:
        print("❌ Fix Groq connection before continuing")
        sys.exit(1)

    # Test 2 — simple classification
    print("\n=== TEST 2 — Simple classification ===")
    response = call_groq(
        prompt="Classify this change in 3 words max: Old text: 'analytics platform'. New text: 'AI-powered analytics platform'",
        system_prompt="You are a competitive intelligence analyst. Be concise.",
        max_tokens=50,
    )
    print(f"Classification response: {response}")

    # Test 3 — reporter style
    print("\n=== TEST 3 — Reporter style ===")
    response = call_groq_reporter(
        prompt="Write one sentence explaining why a competitor adding 'AI-powered' to their homepage matters.",
        system_prompt="You are a competitive intelligence analyst writing for a startup CEO.",
    )
    print(f"Reporter response: {response}")

    print("\n✅ Groq client test complete!")