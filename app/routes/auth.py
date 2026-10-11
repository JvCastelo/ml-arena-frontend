from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.services import api_client
from app.services.api_client import ApiError
from app.services.flash import flash
from app.templates_engine import render

router = APIRouter()


@router.get("/login", name="login_form")
async def login_form(request: Request):
    return render(request, "auth/login.html")


@router.post("/login", name="login_submit")
async def login_submit(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    try:
        token_data = await api_client.login(email, password)
        me = await api_client.get_me(token_data["access_token"])
    except ApiError as exc:
        flash(request, exc.detail, "danger")
        return render(request, "auth/login.html", {"email": email}, status_code=400)

    request.session["access_token"] = token_data["access_token"]
    request.session["user_name"] = me["name"]
    flash(request, f"Bem-vindo, {me['name']}!", "success")
    return RedirectResponse(url=request.url_for("runs_list"), status_code=303)


@router.get("/register", name="register_form")
async def register_form(request: Request):
    return render(request, "auth/register.html")


@router.post("/register", name="register_submit")
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        await api_client.register(name, email, password)
    except ApiError as exc:
        flash(request, exc.detail, "danger")
        return render(
            request,
            "auth/register.html",
            {"name": name, "email": email},
            status_code=400,
        )

    flash(request, "Conta criada! Faça login.", "success")
    return RedirectResponse(url=request.url_for("login_form"), status_code=303)


@router.post("/logout", name="logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=request.url_for("login_form"), status_code=303)
