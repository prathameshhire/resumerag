from typing import Any

import httpx

from app.config import get_settings


class OllamaError(Exception):
    pass


class OllamaService:
    def __init__(self, base_url: str | None = None, model_name: str | None = None, timeout_seconds: int | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model_name = model_name or settings.ollama_model
        self.timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise OllamaError("Ollama server is not reachable.") from exc
        except httpx.TimeoutException as exc:
            raise OllamaError("Ollama model list request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaError(f"Ollama returned status {exc.response.status_code}.") from exc
        except httpx.HTTPError as exc:
            raise OllamaError("Ollama request failed.") from exc

        payload = response.json()
        models = payload.get("models", [])
        return [model.get("name") or model.get("model") for model in models if model.get("name") or model.get("model")]

    def model_is_available(self, available_models: list[str] | None = None) -> bool:
        models = available_models if available_models is not None else self.list_models()
        requested = self.model_name

        if ":" in requested:
            return requested in models

        return any(model == requested or model == f"{requested}:latest" for model in models)

    def chat(self, messages: list[dict[str, str]]) -> str:
        body: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=body, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise OllamaError("Ollama server is not reachable.") from exc
        except httpx.TimeoutException as exc:
            raise OllamaError("Ollama chat request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_detail(exc.response)
            raise OllamaError(detail or f"Ollama returned status {exc.response.status_code}.") from exc
        except httpx.HTTPError as exc:
            raise OllamaError("Ollama request failed.") from exc

        payload = response.json()
        content = payload.get("message", {}).get("content")
        if not isinstance(content, str):
            raise OllamaError("Ollama returned a malformed chat response.")

        return content

    def health(self) -> tuple[bool, bool, str | None]:
        try:
            models = self.list_models()
        except OllamaError as exc:
            return False, False, str(exc)

        model_available = self.model_is_available(models)
        if not model_available:
            return False, False, f"Ollama is reachable, but model '{self.model_name}' was not found."

        return True, True, None

    def _extract_error_detail(self, response: httpx.Response) -> str | None:
        try:
            payload = response.json()
        except ValueError:
            return None

        detail = payload.get("error") or payload.get("detail")
        return detail if isinstance(detail, str) else None
