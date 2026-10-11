# ML Arena — Frontend

Interface web do **ML Arena**, uma ferramenta para registrar execuções ("runs") de modelos de
Machine Learning, acompanhar métricas e hiperparâmetros, e comparar dois runs lado a lado
(incluindo os gráficos de medido×previsto e resíduos gerados a partir do CSV enviado).

Projeto desenvolvido para a disciplina **Desenvolvimento de Software para Nuvem** (UFC).

## Arquitetura: por que dois repositórios

A aplicação é dividida em dois serviços independentes:

- **`ml-arena-backend`**: a API (FastAPI). Guarda os dados em PostgreSQL (RDS), armazena CSVs e
  gráficos no S3, processa o CSV de forma assíncrona num worker separado (SNS/SQS), autentica
  usuários via JWT, audita ações no DynamoDB e usa Redis/ElastiCache como cache. É ele quem fala
  com toda a infraestrutura AWS.
- **`ml-arena-frontend`** (este repositório): só a interface — renderiza as telas e repassa as
  ações do usuário pra API do backend. Não guarda dados, não fala com RDS/S3/DynamoDB/SQS
  diretamente, e não precisa de nenhuma credencial AWS pra funcionar.

Essa separação permite que cada serviço escale e seja implantado de forma independente.

### Como os dois se comunicam

O frontend é um cliente HTTP da API: todas as chamadas (login, listar/criar/remover runs, upload
de CSV, comparação) são feitas pelo próprio servidor do frontend usando `httpx`, nunca pelo
JavaScript do navegador. Isso importa por dois motivos:

1. **Segurança**: o token JWT devolvido pela API no login fica guardado só na sessão do servidor
   (um cookie assinado, graças ao `SessionMiddleware` do Starlette) — o navegador nunca tem acesso
   direto a ele via JavaScript.
2. **Simplicidade**: como o navegador nunca chama a API diretamente, não é preciso configurar CORS
   no backend.

## Stack

- **FastAPI** + **Jinja2** para renderizar o HTML no servidor.
- **Bootstrap** via CDN para o layout — sem build step, sem `npm`/`webpack`.
- **JavaScript puro**, usado só na tela de comparação (`app/static/js/compare.js`), pra buscar os
  dados dos dois runs escolhidos e montar a tabela/plots sem recarregar a página.
- **httpx** como cliente HTTP assíncrono para falar com a API.
- **uv** para gerenciar dependências Python.

## Telas

| Rota | O que faz |
|---|---|
| `/register`, `/login`, `/logout` | Cadastro e autenticação. O token da API fica na sessão. |
| `/runs` | Lista os runs do usuário logado, com status (`created`/`processing`/`done`/`failed`). |
| `/runs/new` | Cria um run (algoritmo, hiperparâmetros, métricas) e, opcionalmente, já envia o CSV medido×previsto. |
| `/runs/{id}/upload` | Envia o CSV depois, para um run que já existe mas ainda não tem um. |
| `/compare` | Tela de comparação ("Model Battle"): escolhe dois runs, clica em **SUBMIT** e vê hiperparâmetros, métricas e os dois gráficos lado a lado. |

O upload de CSV dispara o processamento assíncrono no backend — o run fica `processing` até o
worker terminar de gerar os gráficos, e passa a `done` (ou `failed`, se o CSV não puder ser
processado). Enquanto um gráfico ainda não existe, a tela de comparação avisa em vez de mostrar
uma imagem quebrada.

## Configuração (`.env`)

```bash
cp .env.example .env
```

| Variável | O que é |
|---|---|
| `API_BASE_URL` | Endereço da API do backend (ex.: `http://127.0.0.1:8000` local, ou o DNS do Load Balancer do backend em produção — nunca o IP de uma instância específica). |
| `SECRET_KEY` | Chave usada só para assinar o cookie de sessão deste frontend (via `itsdangerous`). **Não é** a mesma chave que o backend usa para assinar o JWT — são segredos independentes, com finalidades diferentes. Em produção precisa ser um valor aleatório de verdade, gerado com `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`. |

## Como rodar

### Com `uv` (desenvolvimento)

```bash
uv sync
uv run fastapi dev app/main.py --port 8001
```

### Com Docker

```bash
docker build -t ml-arena-frontend .
docker run -d --name frontend --env-file .env -p 8001:8001 --restart unless-stopped ml-arena-frontend
```

Em ambos os casos, a aplicação precisa do backend já rodando e acessível no endereço configurado
em `API_BASE_URL`. Depois de subir, acesse `http://localhost:8001` (ou o endereço da instância,
em produção).

## Deploy

O frontend roda numa única instância EC2, sem Auto Scaling — diferente da API, ele não lida com
carga variável que justifique escalar automaticamente. Não precisa de nenhuma IAM role: como não
faz nenhuma chamada à AWS, só precisa de rede liberada para falar HTTP com o Load Balancer da API.
