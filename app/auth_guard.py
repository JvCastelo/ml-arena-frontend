"""Protege rotas que precisam de login. `require_token` levanta `LoginRequired`
quando não há token na sessão; o handler em `app/main.py` converte isso num
redirect pra tela de login (ver docs/frontend-notes.md pra o porquê da sessão
guardar o JWT em vez do browser)."""

from fastapi import Request


class LoginRequired(Exception):
    pass


def require_token(request: Request) -> str:
    token = request.session.get("access_token")
    if not token:
        raise LoginRequired
    return token
