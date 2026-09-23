# ml-arena-frontend

Protótipo navegável, com **dados mock em memória** (nenhuma chamada a um backend real ainda) —
ver `docs/frontend-notes.md` pra contexto/decisões em aberto.

## Rodar localmente

```bash
uv sync
uv run python run.py
```

Abre em http://127.0.0.1:5000. Os dados resetam a cada restart do processo.

## O que tem

- `/runs` — lista de runs (mock).
- `/runs/new` — form de criação (upload de CSV desabilitado, depende do backend).
- `/compare` — tela "Model Battle": dois slots, seletor de run em cada um, toggle
  predict-plot/resíduos, tabela de comparação com destaque na métrica pior. É a única tela com
  JS próprio (`app/static/js/compare.js`), o resto é só Flask + Jinja2 + Bootstrap.

Sem autenticação — a decisão de sessão/JWT ainda não foi tomada (ver `docs/frontend-notes.md`).
