from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.auth_guard import require_token
from app.services import api_client, mock_plots
from app.templates_engine import render

router = APIRouter(prefix="/compare")

# O backend ainda não gera plots de verdade (sem S3/worker ainda) — os
# gráficos aqui são só ilustrativos, qualidade fixa, até existir plot real.
PLACEHOLDER_QUALITY = 0.65


@router.get("", name="compare_battle")
async def battle(request: Request):
    token = require_token(request)
    data = await api_client.list_runs(token, limit=100)
    return render(request, "compare.html", {"runs": data["items"]})


def _serialize(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": run["id"],
        "name": run["name"],
        "algorithm": run["algorithm"],
        "hyperparams": run["hyperparams"],
        "metrics": run["metrics"],
        "plots": {
            "measured_predicted": f"/compare/plot/{run['id']}/measured_predicted",
            "residuals": f"/compare/plot/{run['id']}/residuals",
        },
        "plots_are_placeholder": True,
    }


@router.get("/data", name="compare_data")
async def data(request: Request, a: int | None = None, b: int | None = None):
    """Mimetiza o payload que `GET /api/v1/runs/compare?a=&b=` vai devolver
    quando existir no backend — hoje monta com duas chamadas a `GET
    /runs/{id}` (hiperparams/métricas reais; plots continuam mock)."""
    token = require_token(request)
    result: dict[str, Any] = {}
    for slot, run_id in (("a", a), ("b", b)):
        if not run_id:
            result[slot] = None
            continue
        run = await api_client.get_run(token, run_id)
        result[slot] = _serialize(run)
    return JSONResponse(result)


@router.get("/plot/{run_id}/{kind}", name="compare_plot")
async def plot(run_id: int, kind: str):
    if kind == "measured_predicted":
        svg = mock_plots.measured_predicted_svg(run_id, PLACEHOLDER_QUALITY)
    elif kind == "residuals":
        svg = mock_plots.residuals_svg(run_id, PLACEHOLDER_QUALITY)
    else:
        return Response(status_code=404)
    return Response(content=svg, media_type="image/svg+xml")
