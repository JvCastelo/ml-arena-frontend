# Contexto do projeto — ML Arena Frontend

Lido automaticamente por qualquer sessão do Claude Code aberta neste repositório. Escrito pelo
Arthur (e pelo Claude da sessão dele) depois que o backend terminou RDS, S3, DynamoDB, SNS/SQS,
ElastiCache e ALB+Auto Scaling — tudo testado em produção na AWS. **Esse arquivo documenta o que
mudou no backend desde `docs/frontend-notes.md` e dá o passo a passo do que falta fazer aqui.**

## O que já está pronto aqui (não precisa tocar)

Auth (`/login`, `/register`, `/logout`), listagem/criação/remoção de runs (`/runs`) — tudo real,
testado ponta a ponta contra o backend. `app/services/api_client.py` já acerta os contratos de
auth e CRUD. Não precisa mudar nada nessa parte.

## O que falta: ligar a comparação e o upload de CSV no backend real

Quando `docs/frontend-notes.md` foi escrito, o backend **não tinha** `GET /runs/compare`, upload
de CSV, S3 nem worker — por isso a tela de comparação usa plots SVG mockados
(`app/services/mock_plots.py`) e o upload está desabilitado no form. **Isso mudou**: as três
coisas existem, estão testadas em produção (RDS + S3 + SNS/SQS + worker gerando os PNGs de
verdade), e é isso que você vai conectar agora.

### 1. `GET /api/v1/runs/compare` — troque as duas chamadas por uma

Hoje `app/routes/compare.py` (`compare_data`) faz **duas** chamadas, uma por slot:
`GET /api/v1/runs/{id}`. Existe uma rota só, pronta pra isso:

```
GET /api/v1/runs/compare?run_a={id}&run_b={id}
```

**Atenção aos nomes dos query params: são `run_a` e `run_b`, não `a`/`b`.** São obrigatórios os
dois juntos — não dá pra mandar um só (a rota do backend não aceita parâmetro ausente). Se o
usuário só escolheu um slot no frontend, continue tratando isso aqui (não chame a rota do backend
até ter os dois ids).

Resposta (`RunComparison`):
```json
{
  "run_a": {
    "id": 5, "name": "xgb-v1", "algorithm": "XGBoost",
    "hyperparams": {"max_depth": 6}, "metrics": {"train": {"rmse": 0.91}, "test": {"rmse": 1.12}},
    "status": "done", "error_message": null, "processing_duration_s": 3.2,
    "created_at": "...", "updated_at": "...",
    "plots": {
      "measured_predicted": "https://....s3.amazonaws.com/...&Signature=...",
      "residuals": "https://....s3.amazonaws.com/...&Signature=..."
    }
  },
  "run_b": { "...": "mesma forma" }
}
```

As chaves de `plots` já são `measured_predicted` e `residuals` — **exatamente os mesmos nomes**
que `app/static/js/compare.js` já usa em `data-plot-kind` e `state.plotKind`. Não precisa mudar a
nomenclatura em nenhum lugar, só a origem do dado.

**Se o plot ainda não foi gerado** (run com CSV subido mas o worker ainda não terminou, ou
`status == "processing"`/`"failed"`), o valor daquela chave em `plots` vem **`null`**, não uma URL
quebrada. Trate isso no JS: hoje `renderPanel` monta `<img src="${plotUrl}">` direto — se
`plotUrl` for `null`, isso quebra a imagem. Troque por algo como "Gráfico ainda sendo gerado,
atualize a página em alguns segundos" quando `plotUrl` for `null`, em vez do `<img>`.

404 se algum dos dois runs não existir ou não for do usuário logado (mesma regra de sempre).

**Passo a passo:**
1. Em `app/services/api_client.py`, adicione uma função `compare_runs(token, run_a, run_b)` que
   chama `GET /api/v1/runs/compare` com esses dois query params e devolve o JSON.
2. Em `app/routes/compare.py`, troque a rota `/compare/data` pra chamar essa função nova em vez
   de duas chamadas a `get_run`. Mantenha os dois ids opcionais (se faltar um, não chame o
   backend — devolva os slots vazios, igual já faz hoje).
3. Apague a rota `/compare/plot/{run_id}/{kind}` e o `app/services/mock_plots.py` — não são mais
   necessários, as URLs agora vêm prontas no JSON.
4. Em `_serialize` (ou o que sobrar dela), use `run["plots"]` direto em vez de montar a URL da
   rota de mock. Pode remover o campo `plots_are_placeholder` (ou recalculá-lo como "ainda
   processando" quando algum dos dois plots vier `null`, se quiser manter um aviso na UI).
5. No `compare.js`, trate `plotUrl === null` como descrito acima.
6. Atualize o texto em `compare.html` (linha "Os gráficos ainda são ilustrativos...") — não é
   mais verdade.

### 2. `POST /api/v1/runs/{run_id}/measured-predicted` — upload do CSV

Hoje desabilitado no form (`app/templates/runs/form.html`, `<input type="file" disabled>`).
Existe de verdade agora:

```
POST /api/v1/runs/{run_id}/measured-predicted
Content-Type: multipart/form-data
campo do arquivo: "file"
```

Regras que o backend aplica (pra você saber que erro esperar, e passar pro usuário):
- Nome do arquivo precisa terminar em `.csv`, senão `422`.
- Limite de **5 MB** (`MAX_CSV_BYTES`); passou disso, `413`.
- Conteúdo precisa ter as colunas `measured` e `predicted`, valores numéricos finitos, pelo menos
  uma linha de dados — senão `422` com mensagem específica da linha/coluna que falhou (útil pra
  mostrar direto pro usuário, o backend já formata bonito, tipo `"Linha 4: 'predicted' precisa
  ser numérico, mas veio 'abc'."`).
- Só um CSV por run: se já tiver um `done`, `409`. Se o upload anterior falhou, pode tentar de
  novo no mesmo run (o backend reaproveita o artifact).

Resposta `201` é o `ArtifactRead` do CSV (não do run):
```json
{"id": 12, "type": "csv_measured_predicted", "status": "done", "size_bytes": 2048,
 "error_message": null, "created_at": "..."}
```

**Importante — isso é só o upload, não os plots.** A resposta `201` confirma que o CSV chegou no
S3 e o worker foi avisado (SNS→SQS). Os dois PNGs são gerados **depois**, de forma assíncrona; o
`run.status` vai pra `"processing"` e só muda pra `"done"` (ou `"failed"`, se o CSV não puder ser
processado) quando o worker terminar — isso pode levar alguns segundos. Não trate a resposta do
upload como "run pronto pra comparar": a UI vai precisar que o usuário recarregue a página (ou
reabra a tela de comparação) depois de um tempo pra ver os plots aparecerem.

**Passo a passo:**
1. Em `app/templates/runs/form.html`: tire o `disabled` do `<input type="file" name="csv_file">`,
   e adicione `enctype="multipart/form-data"` na tag `<form>` (hoje não tem, porque não tinha
   arquivo nenhum no form).
2. Em `app/services/api_client.py`, adicione `upload_measured_predicted(token, run_id, filename,
   content, content_type)`, usando `files={"file": (filename, content, content_type)}` no
   `httpx.AsyncClient.post` (sem o `json=` que as outras funções usam).
3. Em `app/routes/runs.py` (`new_run_submit`): o upload só pode acontecer **depois** do run
   existir (precisa do `run_id`). Fluxo: 1) `create_run` como já faz hoje, pegue o `id` da
   resposta; 2) se o usuário mandou um arquivo no campo novo, chame
   `api_client.upload_measured_predicted` com esse `run_id`. Se o upload falhar (`ApiError`), o
   run já foi criado — decida se quer manter o run mesmo sem CSV (mais simples, mostra a mensagem
   de erro mas não desfaz a criação) ou apagar o run criado nesse caso (mais complexo, não é
   obrigatório). Recomendo a primeira opção pelo tempo que resta.
4. Considere mostrar o `run.status` na lista (`app/templates/runs/list.html`) — hoje a lista
   provavelmente só mostra nome/algoritmo; com upload assíncrono, o usuário precisa de algum jeito
   de ver se o run está `created` (sem CSV ainda), `processing` (CSV subiu, worker trabalhando),
   `done` (plots prontos) ou `failed`. Não tem rota de "atualizar status" no frontend hoje — um
   botão de recarregar a página já resolve, não precisa de polling/websocket pra esse prazo.

## O que **não** mudou e continua valendo

- Browser nunca fala com o backend direto — sem CORS configurado lá, só dá pra chamar via
  `httpx` do próprio frontend (server-to-server). Não tente `fetch()` direto pro backend no JS.
- JWT continua só na sessão do Starlette (`request.session`), nunca exposto ao browser.
- `API_BASE_URL` em produção deve apontar pro **DNS do Load Balancer do backend**
  (`ml-arena-alb-31932376.us-east-1.elb.amazonaws.com`, porta 80), nunca pro IP de uma instância
  específica — o backend agora escala de 1 a 3 instâncias atrás desse ALB, uma instância fixa
  pode não existir mais a qualquer momento.

## Coisas que ficaram de fora desta rodada (não é pra fazer agora)

- O frontend ainda não tem sua própria tela de "detalhe do run" com progresso do processamento —
  só lista, criação e comparação. Dá pra viver sem isso pro prazo.
- Onde o frontend roda na AWS (EC2 própria? atrás de outro ALB?) ainda não foi decidido — ver
  `docs/frontend-notes.md`, seção "Repo separado". Não é bloqueio pra terminar a integração acima.
