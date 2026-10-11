"""Wrapper fino sobre `httpx` pra falar com o ml-arena-backend (FastAPI).

Nada aqui guarda estado entre requisições — cada função abre seu próprio
`AsyncClient`, recebe o token JWT já pronto (vem da sessão do pedido) e
devolve dict/list direto do JSON da API. O browser nunca chama o backend
direto: só o frontend (server-side) fala com ele.
"""

from typing import Any

import httpx

from app.config import settings


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code >= 400:
        detail = "Erro inesperado no backend."
        try:
            body = response.json()
            detail = body.get("detail", detail)
        except ValueError:
            pass
        raise ApiError(response.status_code, str(detail))


async def login(email: str, password: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
    _raise_for_status(response)
    return response.json()


async def register(name: str, email: str, password: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.post(
            "/api/v1/users/",
            json={"name": name, "email": email, "password": password},
        )
    _raise_for_status(response)
    return response.json()


async def get_me(token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.get("/api/v1/users/me", headers=_auth_headers(token))
    _raise_for_status(response)
    return response.json()


async def list_runs(
    token: str,
    limit: int = 20,
    offset: int = 0,
    algorithm: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if algorithm:
        params["algorithm"] = algorithm
    if status:
        params["status"] = status
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.get(
            "/api/v1/runs", params=params, headers=_auth_headers(token)
        )
    _raise_for_status(response)
    return response.json()


async def get_run(token: str, run_id: int) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.get(
            f"/api/v1/runs/{run_id}", headers=_auth_headers(token)
        )
    _raise_for_status(response)
    return response.json()


async def create_run(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.post(
            "/api/v1/runs", json=payload, headers=_auth_headers(token)
        )
    _raise_for_status(response)
    return response.json()


async def delete_run(token: str, run_id: int) -> None:
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.delete(
            f"/api/v1/runs/{run_id}", headers=_auth_headers(token)
        )
    _raise_for_status(response)


async def compare_runs(token: str, run_a: int, run_b: int) -> dict[str, Any]:
    """`GET /api/v1/runs/compare?run_a=&run_b=` — os dois lados prontos pra
    tela de batalha, plots incluídos (URL pré-assinada do S3, ou `null` se o
    worker ainda não terminou)."""
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=10.0
    ) as client:
        response = await client.get(
            "/api/v1/runs/compare",
            params={"run_a": run_a, "run_b": run_b},
            headers=_auth_headers(token),
        )
    _raise_for_status(response)
    return response.json()


async def upload_measured_predicted(
    token: str,
    run_id: int,
    filename: str,
    content: bytes,
    content_type: str | None,
) -> dict[str, Any]:
    """`POST /api/v1/runs/{run_id}/measured-predicted` — upload do CSV. Não
    espera o worker: a resposta só confirma que o CSV chegou no S3 e o
    processamento foi avisado via SNS/SQS (o run fica `processing` até os
    plots ficarem prontos)."""
    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=30.0
    ) as client:
        response = await client.post(
            f"/api/v1/runs/{run_id}/measured-predicted",
            files={"file": (filename, content, content_type or "text/csv")},
            headers=_auth_headers(token),
        )
    _raise_for_status(response)
    return response.json()
