# ml-arena-frontend

FastAPI + Jinja2 + Bootstrap (CDN) + JS puro só na tela de comparação — conecta de verdade com
o `ml-arena-backend` (auth + CRUD de runs). Ver `docs/frontend-notes.md` pra decisões/contexto.

## Rodar localmente

Precisa do backend rodando (porta 8000 por padrão — ver `ml-arena-backend/README.md`/`CLAUDE.md`
pra `docker compose up -d`, `alembic upgrade head`, `.env` com `SECRET_KEY`/`ALGORITHM`).

```bash
cp .env.example .env     # ajuste API_BASE_URL se o backend não estiver em :8000
uv sync
uv run fastapi dev app/main.py --port 8001
```

Abre http://127.0.0.1:8001. Crie uma conta em `/register`, faça login, e use `/runs` e `/compare`.

## O que tem

- `/register`, `/login`, `/logout` — reais, contra `POST /api/v1/users/` e `POST /api/v1/auth/login`
  do backend. Token JWT guardado na sessão (cookie assinado), nunca exposto ao JS do browser.
- `/runs` — lista/cria/remove runs de verdade (`GET/POST/DELETE /api/v1/runs`).
- `/compare` — tela "Model Battle": hiperparâmetros e métricas vêm de dois `GET /api/v1/runs/{id}`
  reais; os **plots ainda são ilustrativos** (SVG gerado localmente) porque o backend não tem
  upload de CSV/S3/worker ainda. É a única tela com JS próprio (`app/static/js/compare.js`).
- Upload de CSV: desabilitado no form de criação de run — depende de
  `POST /runs/{id}/actual-predicted`, que ainda não existe no backend.
