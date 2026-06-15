# Plano de Migração — Adidas Runners → Postgres + VM Florae

> Migrar o bot Adidas Runners de **AWS Lambda + Google Sheets** para rodar na
> **mesma VM Oracle ARM da Florae, porém em stack 100% isolado** — Docker Compose
> próprio + **Postgres dedicado (`adidas-db`)** + systemd timer. Sem usar
> k3s/Argo/vault/`florae-db`/runner/ghcr da Florae (só base de referência).
>
> Data: 2026-06-14 (revisado 2026-06-15 para isolamento total)

---

## 0. Diagnóstico: estado atual

**Adidas Runners** (`AdidasRunnersVirtualAcitivityGetter/`) — bot Python 3.11:
- Scraping das comunidades/eventos do Adidas Runners via **Selenium + Google Chrome
  headless** (proxy opcional), lê JSON da API.
- Notifica eventos novos no **Telegram** (chat + chat admin).
- Persiste estado no **Google Sheets** (abas `live_activities` / `expired_activities`,
  colunas `id, name, startDate, community`).
- **Roda na AWS**: imagem container (`awslambdaric`) no **Lambda**, disparada por
  **EventBridge Scheduler** (`rate(6 hours)`) → **Step Functions** com retry
  escalonado (30m / 1h / 1h30).

**Florae** (alvo) — VM **Oracle Always Free ARM Ampere A1 (arm64), Oracle Linux 9 (SELinux)**:
- **k3s** single-node + **Argo CD** (GitOps via `florae-gitops`), imagens **arm64** no
  **ghcr.io/florae-solutions**, ingress por **Cloudflare Tunnel**.
- **Camada de dados no HOST** (fora do k8s): **`florae-db` (Postgres 17)**, Redis,
  RabbitMQ na rede `florae-network` (`infra/prod/docker-compose.data.yml`). Bancos
  criados por `init-databases.sh` (via `docker exec`, à prova de SELinux). Pods
  alcançam o banco por `Service/Endpoints` → `IP-do-nó:5432`.
- Backup `pg_dump` → Cloudflare R2; **Sealed Secrets** para segredos.

## 1. Decisões travadas

> **Isolamento total:** mesma VM física da Florae, porém **infra e segredos próprios**.
> Nada de k3s/Argo/vault/`florae-db`/runner/ghcr da Florae — ela é só referência.

| Tema | Decisão |
|---|---|
| Onde roda | **Docker Compose próprio no host** + **systemd timer** (6h). Sem k3s/Argo |
| Armazenamento | **100% Postgres** — **container `adidas-db` dedicado** (não o `florae-db`); `GoogleSheetsService` → `PostgresService` |
| Arquitetura | **arm64** — troca obrigatória de Google Chrome por **Chromium** |
| Segredos | **`.env` próprio só na VM** (chmod 600); aposenta `GOOGLE_CREDENTIALS`/`GOOGLE_SHEET_ID` |
| CI/CD | testes na nuvem → **SSH na VM** (secrets próprios) → **build arm64 nativo na VM** + run. Sem registry |

## 2. ⚠️ Riscos técnicos críticos

1. **Google Chrome NÃO existe para ARM Linux.** O `Dockerfile` atual instala
   `google-chrome-stable` (só x86-64) — **não builda nem roda na VM ARM**.
   Solução: **`chromium` + `chromium-driver`** (pacotes arm64-native do Debian).
2. **`webdriver-manager` quebra no ARM.** `SeleniumWebDriverService` chama
   `ChromeDriverManager().install()` (baixa chromedriver x86 do Google).
   Trocar por caminho fixo `/usr/bin/chromedriver` e `binary_location=/usr/bin/chromium`.
3. **`selenium-wire` (proxy)** — funciona em arm64, mas é a peça mais frágil.
   Se proxy não for essencial, considerar `PROXY_ENABLED=false`.
4. **Memória** — Chrome headless tem pico ~0,5–1 GB. O run é efêmero (sobe, roda, sai).

> Estes 4 pontos são o coração da migração; o resto é encanamento.

## 3. Arquitetura alvo (isolada)

```
  GitHub Actions: pytest ──► SSH na VM (secrets próprios) ──► deploy.sh --run

  VM Oracle (host)
  ├── Florae (k3s, florae-db, Argo, vault...)   ← INTOCADO
  └── adidas-runners  (stack próprio, rede adidas-net)
        ├── adidas-db (Postgres 17, volume dedicado, 127.0.0.1:5433)
        ├── bot (imagem arm64 chromium, build NATIVO na VM)
        │     ├─► Adidas API (scraping)  ├─► Telegram  └─► adidas-db
        └── systemd timer adidas-runners.timer (00/06/12/18h)
```

## 4. Mudanças no código (repo Adidas)

- **`PostgresService.py`** (substitui `GoogleSheetsService`, mesma interface usada
  em `main.py`): conexão via `psycopg` (psycopg3, wheel arm64) com
  `DATABASE_URL` ou `PG_HOST/PORT/DB/USER/PASSWORD`.
  - `addNewActivities(arCommunity)`: insere se `id` não existe **e**
    `start_date > now()`; mantém só os novos em `arCommunity.events` para o Telegram.
    `INSERT ... ON CONFLICT (id) DO NOTHING`.
  - `removePastLiveActivities()`: vira housekeeping opcional (DELETE de antigos) ou
    no-op — "live" passa a ser a query `WHERE start_date > now()`.
- **Esquema único** (substitui as 2 abas):
  ```sql
  CREATE TABLE IF NOT EXISTS activities (
      id          TEXT PRIMARY KEY,
      name        TEXT NOT NULL,
      start_date  TIMESTAMPTZ NOT NULL,
      community   TEXT NOT NULL,
      notified_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );
  CREATE INDEX IF NOT EXISTS idx_activities_start_date ON activities (start_date);
  ```
- **`SeleniumWebDriverService.py`**: remover `ChromeDriverManager().install()` →
  `Service(os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))`;
  `options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")`.
- **`main.py`**: `GoogleSheetsService` → `PostgresService`; remover
  `awslambdaric`/`lambda_handler`.
- **`UtilsService.validateEnvVariables`**: remover `GOOGLE_*`, exigir `PG_*`/`DATABASE_URL`.
- **`requirements.txt`**: remover `gspread`, `oauth2client`, `webdriver-manager`,
  `awslambdaric`; adicionar `psycopg[binary]`.

## 5. Banco de dados — Postgres dedicado (container `adidas-db`)

Não usa o `florae-db`. Um container Postgres próprio (`infrastructure/host/docker-compose.yml`):
- Volume dedicado `adidas_pg_data`; rede `adidas-net`; exposto só em `127.0.0.1:5433`.
- Banco `adidas_runners` e usuário criados pelo próprio container (`POSTGRES_DB`/`POSTGRES_USER`
  do `.env`); a tabela `activities` é criada pela app no startup.
- Backup opcional: `docker exec adidas-db pg_dump -U adidas adidas_runners` num cron próprio.

## 6. Containerização (`Dockerfile`, arm64)

- Base `python:3.11-slim`; **Chromium** (`chromium chromium-driver`), não Google Chrome.
- `ENV CHROME_BIN=/usr/bin/chromium CHROMEDRIVER_PATH=/usr/bin/chromedriver`.
- Sem `awslambdaric`; `ENTRYPOINT ["python", "main.py"]`.
- **Build arm64 nativo na VM** (via `docker compose build`), sem buildx/QEMU.

## 7. CI/CD (GitHub Actions) — SSH + build na VM

Pipeline: `build` (pytest na nuvem) → `deploy` (**SSH na VM**: `scp` do código para
`~/adidas-runners` e roda `infrastructure/host/deploy.sh --run`, que faz build arm64
**nativo na VM**, sobe o `adidas-db`, (re)instala o systemd timer e **executa o bot uma vez**
com os logs no pipeline). Build na VM = pipe rápida, sem emulação.

- Secrets no GitHub (próprios do repo): `VM_SSH_HOST`, `VM_SSH_USER`, `VM_SSH_KEY`, `VM_SSH_PORT` (opc.).
- Segredos da app (Telegram/Postgres) **só no `.env` da VM** — o CI nunca os vê.
- Ver `infrastructure/host/` (`deploy.sh`, `docker-compose.yml`, `systemd/`) e o workflow.

## 8. Agendamento (systemd timer)

`adidas-runners.timer` dispara `adidas-runners.service` (oneshot) às 00/06/12/18h.
O service roda `docker compose run --rm bot` (efêmero — sobe, roda, sai; sem Chrome
residente). `Persistent=true` recupera disparos perdidos (VM desligada).

## 9. Retry (Step Functions → simples)

O retry escalonado 30m/1h/1h30 **não** é replicado 1:1. Substituído por defesa em camadas:
- App-level: `getJsonFromUrl` já tenta 3x + rotaciona proxy + reinicia driver.
- Schedule-level: o próximo ciclo de 6h é o "retry final" — **idempotente** (dedup por `id`).
- Falha real → mensagem de erro no **Telegram admin** (lógica preservada).
- Opcional: `OnFailure=` no systemd para um retry mais cedo.

## 10. Cutover & rollback

1. Setup único na VM: `cp .env.example .env` (preencher) em `infrastructure/host/`.
2. `./deploy.sh --run` → valida Chromium ARM + gravação em `activities` + Telegram.
3. Conferir paridade; deixar o timer rodar 1–2 ciclos.
4. **Desativar AWS**: deletar stack CloudFormation. **Rollback** = re-deploy da stack
   (`infrastructure/template.yaml` mantido como referência; Google Sheets intacto no teste).

## 11. Fases

| Fase | Entrega | Risco |
|---|---|---|
| **F1 — Código** | `PostgresService`, fix Selenium ARM, `requirements`, `main`, env, schema, testes | Médio |
| **F2 — Imagem** | `Dockerfile` chromium arm64; build nativo na VM; smoke | **Alto** |
| **F3 — Stack host** | `docker-compose.yml` (adidas-db + bot), `.env`, systemd timer, `deploy.sh` | Baixo |
| **F4 — CI** | workflow pytest → **SSH + build/run na VM** (logs no pipeline) | Baixo |
| **F5 — Cutover** | `.env` na VM, `deploy.sh --run` valida, timer ativo, desligar AWS | Médio |

> **Maior risco = F2 (Chromium em ARM).** Provar cedo que `chromium` + `selenium`
> rodam headless no arm64 antes de investir no resto (`infrastructure/smoke/run-smoke.sh`).
