# ml-arena-frontend

FastAPI + Jinja2 + Bootstrap (CDN) + JS puro só na tela de comparação — conectado de verdade com
o `ml-arena-backend`: auth, CRUD de runs, upload de CSV e comparação com os plots reais (S3 via
URL pré-assinada). Ver `docs/frontend-notes.md` pra decisões/contexto, e o `CLAUDE.md` deste repo
pra como a integração final foi feita.

## Rodar localmente

Precisa do backend rodando (`docker compose up -d` no `ml-arena-backend` — sobe API, worker, db e
redis; precisa de credenciais AWS válidas no `.env` dele pra S3/SNS/SQS/DynamoDB funcionarem).

```bash
cp .env.example .env     # ajuste API_BASE_URL se o backend não estiver em :8000
uv sync
uv run fastapi dev app/main.py --port 8001
```

Abre http://127.0.0.1:8001. Crie uma conta em `/register`, faça login, e use `/runs` e `/compare`.

Em produção, `API_BASE_URL` deve apontar pro DNS do Load Balancer do backend (não pro IP de uma
instância — o backend escala de 1 a 3 instâncias atrás do ALB).

## O que tem

- `/register`, `/login`, `/logout` — reais, contra `POST /api/v1/users/` e `POST /api/v1/auth/login`
  do backend. Token JWT guardado na sessão (cookie assinado), nunca exposto ao JS do browser.
- `/runs` — lista (com status: `created`/`processing`/`done`/`failed`), cria e remove runs de
  verdade. Criar um run aceita opcionalmente o CSV medido×previsto — sobe pro S3, dispara o
  worker (SNS/SQS) e o run fica `processing` até os plots ficarem prontos.
- `/compare` — tela "Model Battle": hiperparâmetros, métricas e plots vêm de
  `GET /api/v1/runs/compare?run_a=&run_b=`, uma chamada só. Se o worker ainda não terminou de
  gerar algum plot, a API devolve `null` naquela chave e a UI avisa em vez de quebrar a imagem —
  recarregar a página depois resolve. É a única tela com JS próprio (`app/static/js/compare.js`).

Testado de ponta a ponta contra o backend local, incluindo upload de CSV real processado pelo
worker (gerando os PNGs de verdade no S3).
