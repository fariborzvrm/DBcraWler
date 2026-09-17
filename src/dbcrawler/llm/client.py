"""OpenRouter client: chat (with json_schema structured output) + embeddings.

httpx keeps us independent of any LLM SDK; OpenRouter is OpenAI-compatible.
Model IDs always come from Settings (ADR-004).
"""

import json
import time

import httpx

from dbcrawler.config.settings import Settings, get_settings


class LLMError(Exception):
    pass


class ValidationError(LLMError):
    pass


class OpenRouterClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        if not self.settings.openrouter_api_key:
            raise LLMError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = httpx.Client(
            base_url=self.settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/dbcrawler",
                "X-Title": "DBcraWler",
            },
            timeout=self.settings.llm_timeout_seconds,
        )

    def _post_with_retries(self, url: str, payload: dict) -> dict:
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = self._client.post(url, json=payload)
                retriable_status = (
                    response.status_code == 429 or response.status_code >= 500
                )
                if retriable_status and attempt < self.settings.llm_max_retries:
                    time.sleep(3 * (attempt + 1))
                    continue
                response.raise_for_status()
                body = response.json()
                # OpenRouter may return HTTP 200 with an upstream error in the body.
                if "error" in body:
                    detail = str(body["error"].get("message", body["error"]))[:300]
                    metadata = body["error"].get("metadata", {})
                    overloaded = (
                        metadata.get("error_type") == "provider_overloaded"
                        or "overloaded" in detail.lower()
                    )
                    if overloaded and attempt < self.settings.llm_max_retries:
                        time.sleep(3 * (attempt + 1))
                        continue
                    raise LLMError(f"OpenRouter upstream error: {detail}")
                return body
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text[:500]
                raise LLMError(
                    f"OpenRouter HTTP {exc.response.status_code}: {detail}"
                ) from exc
            except httpx.HTTPError as exc:
                if attempt >= self.settings.llm_max_retries:
                    raise LLMError(f"OpenRouter request failed: {exc}") from exc
                time.sleep(2)
        raise LLMError("OpenRouter request failed after retries")

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        schema_name: str = "response",
        temperature: float = 0.0,
    ) -> dict:
        """Return a dict validated against the JSON schema by the model itself.

        Uses OpenStruct-style native json_schema response format (ADR-006).
        """
        payload = {
            "model": self.settings.chat_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        result = self._post_with_retries("/chat/completions", payload)
        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected chat response shape: {result}") from exc

        parsed = self._parse_json_content(content)
        if parsed is not None:
            return parsed

        # The auto-router may route to a model that ignores json_schema.
        # One retry with an explicit JSON-only instruction.
        reminder = (
            f"{user_prompt}\n\nRespond with ONLY a single JSON object matching "
            f"this schema and nothing else. Do not add explanations or code fences.\n{json.dumps(schema)}"
        )
        retry_payload = {
            key: value for key, value in payload.items() if key != "response_format"
        }
        retry_payload["messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": reminder},
        ]
        retry_result = self._post_with_retries("/chat/completions", retry_payload)
        try:
            ret_content = retry_result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected chat response shape: {retry_result}") from exc

        parsed = self._parse_json_content(ret_content)
        if parsed is not None:
            return parsed
        raise ValidationError(
            f"Model returned non-JSON content after retry: {ret_content[:300]}"
        )

    @staticmethod
    def _parse_json_content(content: str) -> dict | None:
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        # Find the outermost JSON object, possibly inside prose or code fences.
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {
            "model": self.settings.embedding_model,
            "input": ["search_document: " + t for t in texts],
            "input_type": "search_document",
        }
        data = self._post_with_retries("/embeddings", payload)
        try:
            items = data["data"]
            return [item["embedding"] for item in items]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Unexpected embeddings response shape: {data}") from exc

    def embed_query(self, question: str) -> list[float]:
        payload = {
            "model": self.settings.embedding_model,
            "input": ["search_query: " + question],
            "input_type": "search_query",
        }
        data = self._post_with_retries("/embeddings", payload)
        try:
            return data["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected embeddings response shape: {data}") from exc

    def close(self) -> None:
        self._client.close()
