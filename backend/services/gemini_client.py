"""Gemini API client with structured output and retry logic."""

import json
import structlog
from typing import Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from backend.config import settings


logger = structlog.get_logger()

T = TypeVar('T', bound=BaseModel)


class GeminiClient:
    """Client for Google Gemini API with structured output support."""

    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.model = genai.GenerativeModel(self.model_name)

        # Safety settings - allow research content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        logger.info("gemini_client_initialized", model=self.model_name)

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> Optional[T]:
        """
        Generate structured output conforming to a Pydantic schema.

        Args:
            prompt: The prompt to send to Gemini
            response_schema: Pydantic model class for response validation
            temperature: Generation temperature (0.0 - 1.0)
            max_retries: Maximum number of retry attempts

        Returns:
            Validated Pydantic model instance or None on failure
        """
        # Build prompt with JSON schema instructions
        schema_json = response_schema.model_json_schema()

        full_prompt = f"""{prompt}

You must respond with ONLY valid JSON that conforms to this schema:

{json.dumps(schema_json, indent=2)}

Do not include any explanatory text before or after the JSON.
Respond with valid JSON only."""

        for attempt in range(max_retries):
            try:
                logger.info(
                    "gemini_request",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    temperature=temperature
                )

                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        candidate_count=1,
                    ),
                    safety_settings=self.safety_settings
                )

                # Extract text response
                if not response.text:
                    logger.warning("empty_response_from_gemini", attempt=attempt + 1)
                    continue

                text = response.text.strip()

                # Try to extract JSON if wrapped in markdown
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

                # Parse and validate JSON
                data = json.loads(text)
                validated = response_schema.model_validate(data)

                logger.info(
                    "gemini_success",
                    attempt=attempt + 1,
                    response_size=len(text)
                )

                return validated

            except json.JSONDecodeError as e:
                logger.warning(
                    "json_parse_error",
                    attempt=attempt + 1,
                    error=str(e),
                    response_preview=text[:200] if 'text' in locals() else None
                )

            except Exception as e:
                logger.error(
                    "gemini_generation_error",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )

            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(settings.retry_delay)

        logger.error("gemini_max_retries_exceeded", max_retries=max_retries)
        return None

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> Optional[str]:
        """
        Generate free-form text response.

        Args:
            prompt: The prompt to send
            temperature: Generation temperature
            max_retries: Maximum retry attempts

        Returns:
            Generated text or None on failure
        """
        for attempt in range(max_retries):
            try:
                logger.info("gemini_text_request", attempt=attempt + 1)

                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                    ),
                    safety_settings=self.safety_settings
                )

                if response.text:
                    logger.info("gemini_text_success", attempt=attempt + 1)
                    return response.text.strip()

            except Exception as e:
                logger.error(
                    "gemini_text_error",
                    attempt=attempt + 1,
                    error=str(e)
                )

            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(settings.retry_delay)

        logger.error("gemini_text_max_retries_exceeded")
        return None


# Global Gemini client instance
gemini_client = GeminiClient()
