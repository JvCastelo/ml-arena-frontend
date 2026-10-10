from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.auth_guard import require_token
from app.services import api_client
from app.templates_engine import render

router = APIRouter(prefix="/compare")


@router.get("", name="compare_battle")
async def battle(request: Request):
    token = require_token(request)
    data = await api_client.list_runs(token, limit=100)
    return render(request, "compare.html", {"runs": data["items"]})


@router.get("/data", name="compare_data")
async def data(request: Request, a: int | None = None, b: int | None = None):
    """Proxy pra `GET /api/v1/runs/compare?run_a=&run_b=` — exige os dois ids
    juntos (a rota do backend não aceita um só), então só chama quando o
    usuário já escolheu os dois slots."""
    token = require_token(request)
    if not a or not b:
        return JSONResponse({"a": None, "b": None})

    comparison = await api_client.compare_runs(token, a, b)
    result: dict[str, Any] = {"a": comparison["run_a"], "b": comparison["run_b"]}
    return JSONResponse(result)
