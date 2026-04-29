from __future__ import annotations

import httpx

from app.storage.client import StorageClient


def _response(status_code: int, *, json: dict | None = None) -> httpx.Response:
    request = httpx.Request("GET", "http://storage.test")
    return httpx.Response(status_code, json=json, request=request)


def test_ensure_bucket_skips_create_when_bucket_exists(monkeypatch) -> None:
    posts: list[dict] = []

    def fake_get(*args, **kwargs) -> httpx.Response:
        return _response(200)

    def fake_post(*args, **kwargs) -> httpx.Response:
        posts.append(kwargs)
        return _response(201)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(httpx, "post", fake_post)

    StorageClient().ensure_bucket()

    assert posts == []


def test_ensure_bucket_creates_missing_bucket(monkeypatch) -> None:
    posts: list[dict] = []

    def fake_get(*args, **kwargs) -> httpx.Response:
        return _response(404)

    def fake_post(*args, **kwargs) -> httpx.Response:
        posts.append(kwargs)
        return _response(201)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(httpx, "post", fake_post)

    StorageClient().ensure_bucket()

    assert posts
    assert posts[0]["json"]["id"] == StorageClient().settings.storage_bucket


def test_ensure_bucket_treats_racy_duplicate_create_as_success(monkeypatch) -> None:
    def fake_get(*args, **kwargs) -> httpx.Response:
        return _response(404)

    def fake_post(*args, **kwargs) -> httpx.Response:
        return _response(400, json={"code": "BucketAlreadyExists"})

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(httpx, "post", fake_post)

    StorageClient().ensure_bucket()
