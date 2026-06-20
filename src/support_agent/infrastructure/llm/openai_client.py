from __future__ import annotations

from importlib import import_module

from support_agent.domain.exceptions import DependencyInitializationError, LLMRequestError
from support_agent.infrastructure.llm.base import LLMClient


class OpenAIClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        timeout: int = 30,
        temperature: float = 0.0,
        max_tokens: int = 512,
        api_base: str | None = None,
    ) -> None:
        if not api_key:
            raise DependencyInitializationError(
                "OpenAI API key must be provided for OpenAI LLM access."
            )

        try:
            openai = import_module("openai")
        except ModuleNotFoundError as exc:
            raise DependencyInitializationError(
                "The openai package is required for OpenAIClient but is not installed."
            ) from exc

        openai.api_key = api_key
        if api_base:
            openai.api_base = api_base
        self._client = openai
        self._model = model
        self._timeout = timeout
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.ChatCompletion.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
            )
            choice = response.choices[0]
            return choice.message.content.strip()
        except Exception as exc:
            raise LLMRequestError(
                "OpenAI request failed during response generation."
            ) from exc

    def ping(self) -> bool:
        try:
            self._client.Model.retrieve(self._model)
            return True
        except Exception as exc:
            raise LLMRequestError(
                "OpenAI health check failed while validating the model endpoint."
            ) from exc

