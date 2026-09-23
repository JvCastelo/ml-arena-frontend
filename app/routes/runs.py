import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services import mock_data

runs_bp = Blueprint("runs", __name__, url_prefix="/runs")


@runs_bp.get("")
def list_runs():
    return render_template("runs/list.html", runs=mock_data.list_runs())


@runs_bp.route("/new", methods=["GET", "POST"])
def new_run():
    if request.method == "POST":
        name = request.form["name"].strip()
        algorithm = request.form["algorithm"].strip()
        try:
            hyperparams = json.loads(request.form.get("hyperparams") or "{}")
        except json.JSONDecodeError:
            flash("Hiperparâmetros precisam ser um JSON válido.", "danger")
            return render_template("runs/form.html", form=request.form), 400

        metrics = {
            "train": {
                "rmse": float(request.form["train_rmse"]),
                "mae": float(request.form["train_mae"]),
            },
            "test": {
                "rmse": float(request.form["test_rmse"]),
                "mae": float(request.form["test_mae"]),
            },
        }
        mock_data.create_run(name, algorithm, hyperparams, metrics)
        flash(f'Run "{name}" criado (mock, só em memória — reseta ao reiniciar o servidor).', "success")
        return redirect(url_for("runs.list_runs"))

    return render_template("runs/form.html", form={})


@runs_bp.post("/<int:run_id>/delete")
def delete_run(run_id):
    run = mock_data.get_run(run_id)
    mock_data.delete_run(run_id)
    if run:
        flash(f'Run "{run["name"]}" removido (mock).', "info")
    return redirect(url_for("runs.list_runs"))
