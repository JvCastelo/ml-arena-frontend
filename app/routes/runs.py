import json

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse

from app.auth_guard import require_token
from app.services import api_client
from app.services.api_client import ApiError
from app.services.flash import flash
from app.templates_engine import render

router = APIRouter(prefix="/runs")


@router.get("", name="runs_list")
async def list_runs(request: Request):
    token = require_token(request)
    data = await api_client.list_runs(token, limit=100)
    return render(request, "runs/list.html", {"runs": data["items"]})


@router.get("/new", name="new_run_form")
async def new_run_form(request: Request):
    require_token(request)
    return render(request, "runs/form.html", {"form": {}})


@router.post("/new", name="new_run_submit")
async def new_run_submit(
    request: Request,
    name: str = Form(...),
    algorithm: str = Form(...),
    hyperparams: str = Form(""),
    train_rmse: float = Form(...),
    train_mae: float = Form(...),
    test_rmse: float = Form(...),
    test_mae: float = Form(...),
    csv_file: UploadFile | None = File(None),
):
    token = require_token(request)

    try:
        hp = json.loads(hyperparams or "{}")
    except json.JSONDecodeError:
        flash(request, "Hiperparâmetros precisam ser um JSON válido.", "danger")
        return render(
            request,
            "runs/form.html",
            {
                "form": {
                    "name": name,
                    "algorithm": algorithm,
                    "hyperparams": hyperparams,
                }
            },
            status_code=400,
        )

    payload = {
        "name": name,
        "algorithm": algorithm,
        "hyperparams": hp,
        "metrics": {
            "train": {"rmse": train_rmse, "mae": train_mae},
            "test": {"rmse": test_rmse, "mae": test_mae},
        },
    }
    try:
        created = await api_client.create_run(token, payload)
    except ApiError as exc:
        flash(request, exc.detail, "danger")
        return render(
            request,
            "runs/form.html",
            {
                "form": {
                    "name": name,
                    "algorithm": algorithm,
                    "hyperparams": hyperparams,
                }
            },
            status_code=400,
        )

    flash(request, f'Run "{name}" criado.', "success")

    if csv_file is not None and csv_file.filename:
        content = await csv_file.read()
        try:
            await api_client.upload_measured_predicted(
                token, created["id"], csv_file.filename, content, csv_file.content_type
            )
            flash(
                request,
                "CSV enviado — os plots ficam prontos em alguns segundos.",
                "info",
            )
        except ApiError as exc:
            # O run já foi criado; o CSV pode ser enviado depois editando o run.
            flash(
                request,
                f"Run criado, mas o upload do CSV falhou: {exc.detail}",
                "warning",
            )

    return RedirectResponse(url=request.url_for("runs_list"), status_code=303)


@router.post("/{run_id}/delete", name="delete_run")
async def delete_run(request: Request, run_id: int):
    token = require_token(request)
    await api_client.delete_run(token, run_id)
    flash(request, "Run removido.", "info")
    return RedirectResponse(url=request.url_for("runs_list"), status_code=303)
