"""Flash messages via sessão (Starlette não tem `flash()` embutido como o Flask)."""

from fastapi import Request


def flash(request: Request, message: str, category: str = "info") -> None:
    messages = request.session.get("_flashes", [])
    messages.append({"message": message, "category": category})
    request.session["_flashes"] = messages


def get_flashed_messages(request: Request) -> list[dict[str, str]]:
    return request.session.pop("_flashes", [])
