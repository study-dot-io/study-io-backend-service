import openai
import os
import json
import time
import logging
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

@dataclass
class Flashcard:
    """Data class representing a flashcard with front and back content"""
    front: str
    back: str

    def to_dict(self) -> dict:
        """Convert flashcard to dictionary format"""
        return {
            "front": self.front,
            "back": self.back
        }

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

PROMPT_TEMPLATE = """
Generate flashcards from this text. Return a JSON list with 'front' and 'back' keys. Return a max of only 10 flashcards.

Text:
{chunk}

Return only the JSON list, like:
[
  {{"front": "...", "back": "..."}},
  ...
]
"""

class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors"""
    pass

def generate_flashcards(chunk, max_retries=3, retry_delay=2) -> List[Flashcard]:
    """
    Generate flashcards with retry logic and comprehensive error handling

    Args:
        chunk: Text content to generate flashcards from
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (increases exponentially)

    Returns:
        List of Flashcard objects or empty list if all attempts fail
    """
    prompt = PROMPT_TEMPLATE.format(chunk=chunk)

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to generate flashcards (attempt {attempt + 1}/{max_retries})")

            response = openai.ChatCompletion.create(
                model="google/gemini-2.5-flash-lite",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                timeout=30
            )

            content = response.choices[0].message.content.strip()
            if content:
                content = cleanup_content(content)

            flashcards_data = json.loads(content)

            # Convert dictionaries to Flashcard objects
            flashcards = [
                Flashcard(front=card.get("front", ""), back=card.get("back", ""))
                for card in flashcards_data
                if isinstance(card, dict) and card.get("front") and card.get("back")
            ]

            logger.info(f"Successfully generated {len(flashcards)} flashcards")
            return flashcards

        except openai.error.APIError as e:
            error_message = str(e)
            logger.error(f"OpenRouter API Error (attempt {attempt + 1}): {error_message}")

            # Check for specific error types
            if "502" in error_message or "Bad Gateway" in error_message:
                logger.warning("502 Bad Gateway detected - OpenRouter infrastructure issue")
                if attempt < max_retries - 1:
                    sleep_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                else:
                    logger.error("Max retries reached for 502 error")
                    raise OpenRouterError("OpenRouter is experiencing infrastructure issues (502 Bad Gateway). Please try again later.")

            elif "429" in error_message or "rate limit" in error_message.lower():
                logger.warning("Rate limit exceeded")
                if attempt < max_retries - 1:
                    sleep_time = retry_delay * (2 ** attempt) + 5  # Longer wait for rate limits
                    logger.info(f"Rate limited - waiting {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                else:
                    raise OpenRouterError("Rate limit exceeded. Please try again later.")

            else:
                logger.error(f"Unhandled API error: {error_message}")
                raise OpenRouterError(f"API Error: {error_message}")

        except openai.error.Timeout:
            logger.warning(f"Request timeout (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"Retrying after timeout in {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
            else:
                raise OpenRouterError("Request timed out after multiple attempts")

        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")

            # Don't retry JSON errors as they're likely content issues
            return []

        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"Retrying after unexpected error in {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
            else:
                raise OpenRouterError(f"Failed to generate flashcards after {max_retries} attempts: {str(e)}")

    # If we get here, all retries failed
    logger.error("All retry attempts exhausted")
    return []

def cleanup_content(content):
    """Clean up LLM response content to extract JSON"""
    logger.debug("Cleaning up LLM response content")
    if content.startswith("```json"):
        content = content.removeprefix("```json").removesuffix("```").strip()
    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()
    return content

def check_openrouter_health():
    """
    Quick health check for OpenRouter API
    Returns True if healthy, False otherwise
    """
    try:
        openai.ChatCompletion.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
            timeout=10
        )
        return True
    except Exception as e:
        logger.warning(f"OpenRouter health check failed: {e}")
        return False