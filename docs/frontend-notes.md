# Notas de arquitetura do frontend

> Documento de trabalho, no mesmo espírito de `docs/api-contract.md` e `docs/db-diagram.md` no
> repo do backend. Começou como rascunho (seções abaixo marcadas **[histórico]** refletem a
> primeira versão, com Flask) e foi atualizado depois que o backend trocou pra FastAPI e ganhou
> auth real — ver "Decisões agora fechadas" logo abaixo.

## Decisões agora fechadas (atualização pós-migração pra FastAPI)

- **Stack trocada de Flask pra FastAPI** — o próprio `CLAUDE.md` do backend já listava como
  pendência "Frontend (obrigatório): Jinja2 via FastAPI + JS puro na comparação + Bootstrap", ou
  seja, o time já tinha decidido isso. Continua tudo server-rendered (Jinja2) + Bootstrap via CDN
  + JS puro só na tela de comparação — só o framework Python mudou.
- **JWT guardado na sessão do Starlette** (`SessionMiddleware`, cookie assinado por
  `itsdangerous`) — o equivalente direto da sessão do Flask que a seção "decisão em aberto"
  abaixo cogitava. `app/auth_guard.py` protege rotas exigindo login; token nunca chega ao
  browser.
- **Browser nunca fala com o backend direto** — confirmado como o caminho certo: o backend não
  tem `CORSMiddleware` configurado, então uma chamada de JS do browser direto pro FastAPI do
  backend simplesmente falharia. `app/services/api_client.py` centraliza as chamadas
  server-to-server via `httpx`.
- **Auth e CRUD de runs são reais** (ver `ml-arena-backend/CLAUDE.md` e `docs/api-contract.md`
  dele): `POST /api/v1/users/`, `POST /api/v1/auth/login` (form-encoded, campos `username`/
  `password`), `GET /api/v1/users/me`, `POST/GET/PATCH/DELETE /api/v1/runs`. Testado de ponta a
  ponta (registro → login → criar run → listar → comparar → deletar) contra o backend rodando em
  Docker localmente.
- **Tela de comparação é híbrida por enquanto**: hiperparâmetros e métricas vêm de dois `GET
  /api/v1/runs/{id}` reais; os plots continuam sendo SVG gerado localmente
  (`app/services/mock_plots.py`), com um badge "plot ilustrativo" na UI, porque o backend ainda
  não tem `GET /runs/compare`, upload de CSV, S3 nem worker. Quando essas rotas existirem, trocar
  `app/routes/compare.py` pra consumi-las direto (idealmente um único `GET /runs/compare?a=&b=`
  em vez de duas chamadas a `/runs/{id}`).
- **Upload de CSV continua desabilitado** no form de criar run — mesma razão.

## Contexto do backend que importa pra cá

- TP de Desenvolvimento de Software para Nuvem (UFC), prazo 10/10/2026.
- Auth decidida (não implementada ainda): login e-mail+senha, **JWT**, API **stateless** — crítico
  porque o ALB da Parte 2 roteia requisições pra qualquer instância do Auto Scaling Group a
  qualquer momento.
- Modelo de dados fechado: `users`, `runs` (nome, algoritmo, hyperparams JSONB, metrics JSONB
  train/test, status), `artifacts` (CSV + 2 plots PNG por run, com status próprio).
- Telas previstas no spec: lista de runs, criação de run (form + upload de CSV), tela de
  comparação "Model Battle" (dois slots lado a lado, tabela de métricas com destaque pra métrica
  pior, botão SUBMIT chamando `GET /runs/compare?a=&b=`).
- `docs/api-contract.md` do backend ainda **não fechou** os contratos de request/response — não dá
  pra integrar de verdade ainda, só desenhar a UI.
- O `spec.md` original do backend cogitava o frontend *dentro* da mesma app Flask (`templates/` /
  `static/` junto do backend). A existência deste repo separado (`ml-arena-frontend`) já é, na
  prática, uma decisão tomada — vale documentar explicitamente em algum lugar (aqui mesmo, quando
  fechar) o porquê e as consequências dela (ver seção "Repo separado" abaixo).

## [histórico] A escolha original (Flask + Jinja2 + Bootstrap via CDN + JS pontual)

> Primeira versão desta seção, de quando o backend ainda era Flask. O raciocínio (zero toolchain
> JS, Bootstrap via CDN, JS só na comparação) continua todo válido — só o framework mudou de
> Flask pra FastAPI, pelos mesmos motivos listados em "Decisões agora fechadas".

Faz sentido pro contexto: prazo apertado, pouca experiência de frontend, precisa rodar numa EC2
atrás de ALB/ASG.

- **Bootstrap via CDN + Jinja2 sem build step = zero toolchain JS.** Sem npm/webpack/node_modules.
  Isso simplifica de verdade o Dockerfile/deploy na EC2 — elimina uma classe inteira de dor de
  configuração que não compensa aprender sob pressão de prazo.
- Continua sendo um serviço Python: `pyproject.toml` + `uv` + `ruff` se aplicam igual ao backend.
- O que **muda** em relação ao backend: o frontend não fala com RDS/S3/Dynamo diretamente, só
  chama a API do backend e renderiza HTML. Então **não** precisa de `sqlalchemy`, `psycopg`,
  `boto3`.

## Estrutura de pastas atual (pós-migração pra FastAPI)

```
ml-arena-frontend/
├── app/
│   ├── main.py               # instância do FastAPI, SessionMiddleware, exception handlers
│   ├── config.py             # Settings: API_BASE_URL, SECRET_KEY (via env/.env)
│   ├── auth_guard.py         # require_token() — protege rota, redireciona pra /login
│   ├── templates_engine.py   # Jinja2Templates + injeção de flash/user_name
│   ├── routes/
│   │   ├── auth.py           # /login, /register, /logout
│   │   ├── runs.py           # lista, criação, remoção
│   │   └── compare.py        # tela de batalha + /compare/data + /compare/plot (mock)
│   ├── services/
│   │   ├── api_client.py     # httpx.AsyncClient, chamadas ao backend com o Bearer token
│   │   ├── flash.py          # flash()/get_flashed_messages() via sessão (Starlette não tem)
│   │   └── mock_plots.py     # SVG placeholder pros plots, até o backend gerar de verdade
│   ├── templates/
│   │   ├── base.html, auth/, runs/, compare.html
│   └── static/js/compare.js  # o único JS do projeto
├── pyproject.toml
├── .env.example
└── README.md
```

## [histórico] Decisão que estava em aberto: onde fica o JWT

> Resolvida — ver "Decisões agora fechadas" no topo. Ficava assim quando ainda não dava pra
> integrar de verdade (backend não tinha auth implementada): a sessão do framework guarda o JWT,
> o JS da comparação nunca fala com o backend direto. A implementação confirmou que funciona.

## Repo separado do backend — pontos a decidir quando for hora

- Se o frontend for uma app Flask separada rodando em outra porta/instância, **quem fica atrás do
  ALB/ASG da Parte 2**: só o frontend, só o backend, ou os dois (dois ALBs/ASGs)? Isso muda a
  arquitetura de deploy e o vídeo de demonstração da elasticidade.
- Se os dois escalam independentemente, cada instância do frontend precisa da mesma `SECRET_KEY`
  (ver seção acima) e do `API_BASE_URL` apontando pro load balancer do backend, não pra uma
  instância fixa.

## Estado atual

As três telas do spec (lista de runs, criação de run, comparação) estão conectadas de verdade ao
backend — auth, criação/listagem/remoção de runs. Testado de ponta a ponta contra o backend
rodando em Docker (`docker compose up -d` no `ml-arena-backend`). O que falta pro resto virar real
está listado em "Decisões agora fechadas" (plots, upload de CSV) — isso é trabalho do backend
(`GET /runs/compare`, S3, worker), não do frontend.
