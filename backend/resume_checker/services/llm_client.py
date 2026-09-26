import json
import os
from typing import Type, TypeVar, Any

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from groq import Groq

# Load environment variables
load_dotenv()

class LLMConfigurationError(Exception):
    """Raised when LLM configuration is missing or invalid."""
    pass

class LLMResponseError(Exception):
    """Raised when LLM response is invalid or fails schema validation after retries."""
    pass

T = TypeVar('T', bound=BaseModel)

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "groq")
        if self.provider == "groq":
            self.api_key = os.getenv("GROQ_API_KEY")
            if not self.api_key:
                raise LLMConfigurationError("GROQ_API_KEY is not configured in environment.")
            self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
            self._client = Groq(api_key=self.api_key)
        else:
            raise LLMConfigurationError(f"Unsupported LLM provider: {self.provider}")

    def call(self, prompt: str, schema: Type[T]) -> T:
        """
        Call the configured LLM provider with a prompt and a Pydantic schema.
        Retries exactly once on validation/parsing failure.
        """
        retries = 1
        attempts = 0
        last_exception = None

        while attempts <= retries:
            try:
                if self.provider == "groq":
                    return self._call_groq(prompt, schema)
                else:
                    raise LLMConfigurationError(f"Unsupported LLM provider: {self.provider}")
            except (json.JSONDecodeError, ValidationError) as e:
                last_exception = e
                attempts += 1
                if attempts > retries:
                    raise LLMResponseError(
                        f"Failed to get valid response after {retries} retries: {str(e)}"
                    ) from e
            except LLMResponseError as e:
                # If we raised LLMResponseError directly (e.g. empty content)
                last_exception = e
                attempts += 1
                if attempts > retries:
                    raise e
            except Exception as e:
                # Any other API error (e.g., bad request, auth error) should fail immediately
                raise

        raise LLMResponseError(f"Unexpected error: {last_exception}")

    def _enforce_strict_schema(self, schema: dict) -> dict:
        if isinstance(schema, dict):
            if schema.get("type") == "object" and "additionalProperties" not in schema:
                schema["additionalProperties"] = False
            
            # Pydantic may define definitions in $defs
            for key, value in schema.items():
                self._enforce_strict_schema(value)
        elif isinstance(schema, list):
            for item in schema:
                self._enforce_strict_schema(item)
        return schema

    def _call_groq(self, prompt: str, schema: Type[T]) -> T:
        json_schema = schema.model_json_schema()
        json_schema = self._enforce_strict_schema(json_schema)
        schema_name = schema.__name__

        # Groq strict mode requires all properties to be required and no additionalProperties.
        # We will attempt to use strict: True, if schema is properly defined.
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": json_schema
            }
        }

        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format=response_format
        )

        content = response.choices[0].message.content
        if not content:
            raise LLMResponseError("LLM returned empty content.")

        # This will raise ValidationError if the content does not match the schema
        # or JSONDecodeError if it's invalid JSON (handled by Pydantic/json underneath)
        return schema.model_validate_json(content)

# Instantiate the singleton client for the application to use
llm_client = LLMClient()