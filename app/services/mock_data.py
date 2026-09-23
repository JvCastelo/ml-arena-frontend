"""Dados fake em memória — só pra navegar no protótipo, sem backend real.

Reseta a cada restart do processo. Formato dos runs segue docs/db-diagram.md do
ml-arena-backend (hyperparams/metrics como dict livre, igual JSONB).
"""

import itertools
import random
from datetime import datetime, timedelta

_id_counter = itertools.count(1)
_RUNS: list[dict] = []


def _next_id():
    return next(_id_counter)


def _seed():
    now = datetime.utcnow()
    seed_runs = [
        dict(
            name="xgb-baseline",
            algorithm="XGBoost",
            quality=0.85,
            hyperparams={"max_depth": 6, "n_estimators": 300, "learning_rate": 0.05},
            metrics={
                "train": {"rmse": 1.12, "mae": 0.81},
                "test": {"rmse": 1.55, "mae": 1.10},
            },
        ),
        dict(
            name="stm-v1",
            algorithm="STM",
            quality=0.35,
            hyperparams={"window": 12, "seasonal_periods": 24},
            metrics={
                "train": {"rmse": 3.40, "mae": 2.75},
                "test": {"rmse": 4.02, "mae": 3.15},
            },
        ),
        dict(
            name="lgbm-tuned",
            algorithm="LightGBM",
            quality=0.78,
            hyperparams={"num_leaves": 31, "n_estimators": 500, "learning_rate": 0.03},
            metrics={
                "train": {"rmse": 1.30, "mae": 0.95},
                "test": {"rmse": 1.68, "mae": 1.22},
            },
        ),
        dict(
            name="lstm-exp3",
            algorithm="LSTM",
            quality=0.55,
            hyperparams={"hidden_size": 64, "layers": 2, "epochs": 50},
            metrics={
                "train": {"rmse": 2.05, "mae": 1.60},
                "test": {"rmse": 2.61, "mae": 2.02},
            },
        ),
    ]
    for i, r in enumerate(seed_runs):
        run_id = _next_id()
        _RUNS.append(
            {
                "id": run_id,
                "name": r["name"],
                "algorithm": r["algorithm"],
                "hyperparams": r["hyperparams"],
                "metrics": r["metrics"],
                "status": "done",
                "quality": r["quality"],
                "created_at": now - timedelta(days=len(seed_runs) - i),
            }
        )


_seed()


def list_runs():
    return sorted(_RUNS, key=lambda r: r["created_at"], reverse=True)


def get_run(run_id):
    return next((r for r in _RUNS if r["id"] == run_id), None)


def create_run(name, algorithm, hyperparams, metrics):
    run = {
        "id": _next_id(),
        "name": name,
        "algorithm": algorithm,
        "hyperparams": hyperparams,
        "metrics": metrics,
        "status": "done",
        "quality": random.uniform(0.3, 0.9),
        "created_at": datetime.utcnow(),
    }
    _RUNS.append(run)
    return run


def delete_run(run_id):
    global _RUNS
    _RUNS = [r for r in _RUNS if r["id"] != run_id]
