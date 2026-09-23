# Notas de arquitetura do frontend — rascunho, nada decidido

> Documento de trabalho, no mesmo espírito de `docs/api-contract.md` e `docs/db-diagram.md` no
> repo do backend: ponto de partida pra decidir com calma, não uma decisão fechada. Escrito numa
> conversa com o Claude depois de ler o `ml-arena-backend` inteiro (README vazio, `CLAUDE.md`,
> `docs/spec.md`, `docs/api-contract.md`, `docs/db-diagram.md`, `pyproject.toml`).

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

## A escolha (Flask + Jinja2 + Bootstrap via CDN + JS pontual só na comparação)

Faz sentido pro contexto: prazo apertado, pouca experiência de frontend, precisa rodar numa EC2
atrás de ALB/ASG.

- **Bootstrap via CDN + Jinja2 sem build step = zero toolchain JS.** Sem npm/webpack/node_modules.
  Isso simplifica de verdade o Dockerfile/deploy na EC2 — elimina uma classe inteira de dor de
  configuração que não compensa aprender sob pressão de prazo.
- Continua sendo um serviço Python: `pyproject.toml` + `uv` + `ruff` se aplicam igual ao backend.
- O que **muda** em relação ao backend: o frontend não fala com RDS/S3/Dynamo diretamente, só
  chama a API do backend e renderiza HTML. Então **não** precisa de `sqlalchemy`, `psycopg`,
  `boto3`. Precisa de:
  ```toml
  dependencies = [
      "flask>=3.1.3",
      "requests>=2.32",       # chamar a API do backend
      "python-dotenv>=1.2.3",
  ]
  ```
  (Jinja2 já vem embutido no Flask.)

## Estrutura de pastas sugerida

```
ml-arena-frontend/
├── app/
│   ├── __init__.py          # factory do Flask
│   ├── config.py            # API_BASE_URL, SECRET_KEY (via env)
│   ├── routes/
│   │   ├── auth.py          # /login, /register (views)
│   │   ├── runs.py          # lista, criação, edição, upload
│   │   └── compare.py       # tela de batalha
│   ├── services/
│   │   └── api_client.py    # wrapper fino sobre `requests`, injeta o JWT
│   ├── templates/
│   │   ├── base.html        # Bootstrap via CDN, navbar
│   │   ├── runs/
│   │   └── compare.html
│   └── static/
│       └── js/
│           └── compare.js   # o JS pontual da tela de comparação
├── pyproject.toml
├── .env.example
└── README.md
```

## Decisão em aberto: onde fica o JWT, e como o JS da comparação busca dado

Como o backend é stateless (JWT), o frontend precisa decidir onde guardar o token depois do login,
e como o JS da tela de comparação busca os dados sem expor token nem a URL do backend no browser.

**Recomendação (não decidida ainda):** sessão do Flask (cookie assinado) guarda o JWT depois do
login — continua compatível com Auto Scaling, desde que `SECRET_KEY` venha de variável de ambiente
**igual em todas as instâncias** (não gerada em memória a cada boot). O `api_client.py` lê o JWT da
sessão em cada request pro backend. O JS da tela de comparação **não chama o backend direto** —
chama uma rota própria do frontend (ex.: `GET /compare/data?a=&b=`) que faz proxy pro backend
usando o JWT da sessão. Isso evita CORS e evita vazar o token pro JS do browser.

## Repo separado do backend — pontos a decidir quando for hora

- Se o frontend for uma app Flask separada rodando em outra porta/instância, **quem fica atrás do
  ALB/ASG da Parte 2**: só o frontend, só o backend, ou os dois (dois ALBs/ASGs)? Isso muda a
  arquitetura de deploy e o vídeo de demonstração da elasticidade.
- Se os dois escalam independentemente, cada instância do frontend precisa da mesma `SECRET_KEY`
  (ver seção acima) e do `API_BASE_URL` apontando pro load balancer do backend, não pra uma
  instância fixa.

## Protótipo

Existe um protótipo navegável em `app/` (branch/estado inicial deste repo) rodando com **dados
mock em memória**, sem chamar nenhum backend real — só pra visualizar as três telas do spec (lista
de runs, criação de run, comparação) e pensar em botões/fluxos que faltam. Ver `README.md` pra
rodar localmente. Ele não implementa login (a decisão de sessão/JWT acima ainda não foi tomada) e
os dados resetam a cada restart do processo — é só ferramenta de rascunho visual, não é o começo
"oficial" da implementação real.
