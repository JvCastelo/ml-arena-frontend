from flask import Blueprint, Response, jsonify, render_template, request

from ..services import mock_data, mock_plots

compare_bp = Blueprint("compare", __name__, url_prefix="/compare")


@compare_bp.get("")
def battle():
    return render_template("compare.html", runs=mock_data.list_runs())


def _serialize(run):
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
    }


@compare_bp.get("/data")
def data():
    """Mimetiza o payload combinado que `GET /runs/compare?a=&b=` vai devolver
    no backend real — hoje montado aqui a partir dos dados mock."""
    result = {}
    for slot in ("a", "b"):
        run_id = request.args.get(slot, type=int)
        run = mock_data.get_run(run_id) if run_id else None
        result[slot] = _serialize(run) if run else None
    return jsonify(result)


@compare_bp.get("/plot/<int:run_id>/<kind>")
def plot(run_id, kind):
    run = mock_data.get_run(run_id)
    if not run:
        return "", 404
    if kind == "measured_predicted":
        svg = mock_plots.measured_predicted_svg(run_id, run["quality"])
    elif kind == "residuals":
        svg = mock_plots.residuals_svg(run_id, run["quality"])
    else:
        return "", 404
    return Response(svg, mimetype="image/svg+xml")
