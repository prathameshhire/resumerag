import httpx

from app.services.ollama_service import OllamaError, OllamaService


def test_model_matching_accepts_tagless_requested_name() -> None:
    service = OllamaService(base_url="http://ollama", model_name="llama3.2")

    assert service.model_is_available(["llama3.2:latest"])
    assert not service.model_is_available(["llama3.2:3b"])


def test_model_matching_requires_exact_tag_when_requested() -> None:
    service = OllamaService(base_url="http://ollama", model_name="llama3.2:3b")

    assert service.model_is_available(["llama3.2:3b"])
    assert not service.model_is_available(["llama3.2:latest"])


def test_chat_extracts_assistant_content(monkeypatch) -> None:
    def fake_post(*_: object, **__: object) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "ok"}}, request=httpx.Request("POST", "http://ollama/api/chat"))

    monkeypatch.setattr(httpx, "post", fake_post)

    service = OllamaService(base_url="http://ollama", model_name="llama3.2")

    assert service.chat([{"role": "user", "content": "hello"}]) == "ok"


def test_chat_rejects_malformed_response(monkeypatch) -> None:
    def fake_post(*_: object, **__: object) -> httpx.Response:
        return httpx.Response(200, json={"message": {}}, request=httpx.Request("POST", "http://ollama/api/chat"))

    monkeypatch.setattr(httpx, "post", fake_post)
    service = OllamaService(base_url="http://ollama", model_name="llama3.2")

    try:
        service.chat([{"role": "user", "content": "hello"}])
    except OllamaError as exc:
        assert "malformed" in str(exc)
    else:
        raise AssertionError("Expected OllamaError")
