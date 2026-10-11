from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth_guard import LoginRequired
from app.config import settings
from app.routes import auth, compare, runs
from app.services.api_client import ApiError
from app.services.flash import flash

app = FastAPI(title="ML Arena Frontend")
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(runs.router)
app.include_router(compare.router)


@app.get("/", name="index")
async def index():
    return RedirectResponse(url="/runs")


@app.exception_handler(LoginRequired)
async def handle_login_required(request: Request, exc: LoginRequired):
    return RedirectResponse(url=request.url_for("login_form"), status_code=303)


@app.exception_handler(ApiError)
async def handle_api_error(request: Request, exc: ApiError):
    if exc.status_code == 401:
        request.session.clear()
        flash(request, "Sessão expirada, faça login novamente.", "warning")
        return RedirectResponse(url=request.url_for("login_form"), status_code=303)
    flash(request, exc.detail, "danger")
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)
