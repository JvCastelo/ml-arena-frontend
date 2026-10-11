from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.services.flash import get_flashed_messages

templates = Jinja2Templates(directory="app/templates")


def render(
    request: Request,
    name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
):
    """`TemplateResponse` com `messages` (flash) e `user_name` sempre injetados,
    pra não repetir isso em toda rota."""
    ctx = dict(context or {})
    ctx["messages"] = get_flashed_messages(request)
    ctx["user_name"] = request.session.get("user_name")
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
