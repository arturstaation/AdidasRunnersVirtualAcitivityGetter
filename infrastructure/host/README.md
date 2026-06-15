# Deploy — Adidas Runners (stack isolado na VM)

Roda na **mesma VM** da Florae, mas com **infra e segredos 100% próprios**: container
Postgres dedicado (`adidas-db`), rede/volume próprios e agendamento por **systemd timer**
(a cada 6h). **Não** usa k3s, Argo, vault nem o `florae-db`. Florae é só referência.

```
VM Oracle (host)
├── Florae (k3s + florae-db + ...)        ← intocado
└── adidas-runners (este stack)
      ├── adidas-db (Postgres 17)  ── rede adidas-net ──┐
      ├── bot (imagem arm64, Chromium)  ◄───────────────┘  run a cada 6h
      └── systemd timer adidas-runners.timer
```

## Setup único na VM

```bash
# 1. tenha o código na VM (o CI joga em ~/adidas-runners; manualmente: git clone)
cd ~/adidas-runners/infrastructure/host

# 2. crie o .env (fica SÓ na VM; o CI nunca envia segredos)
cp .env.example .env && chmod 600 .env
nano .env        # PG_PASSWORD, TOKEN, CHAT_ID, ADMIN_CHAT_ID...

# 3. primeiro deploy + run
./deploy.sh --run
```

O `deploy.sh`: build arm64 nativo → sobe o `adidas-db` → instala/ativa o timer →
(com `--run`) executa o bot uma vez e mostra os logs. A tabela `activities` é criada
pela app no primeiro run; o banco `adidas_runners` é criado pelo próprio container.

## Deploy automático (CI)

Configure 3 secrets no repo (Settings → Secrets → Actions) e **todo push na `main`**
testa → SSH na VM → envia o código → `deploy.sh --run` (build arm64 nativo na VM, rápido):

| Secret | Para quê |
|---|---|
| `VM_SSH_HOST` | IP/host da VM (ex.: `163.192.45.157`) |
| `VM_SSH_USER` | usuário SSH (ex.: `opc`) |
| `VM_SSH_KEY`  | chave privada SSH (PEM) |
| `VM_SSH_PORT` | opcional, default 22 |

Os segredos da app (Telegram, senha do Postgres) **não** entram no GitHub — vivem só no
`.env` da VM. O `scp` não sobrescreve o `.env` (ele não está no repo).

## Operação

```bash
cd ~/adidas-runners/infrastructure/host
docker compose run --rm bot                 # run manual avulso
systemctl list-timers adidas-runners.timer  # quando dispara
journalctl -u adidas-runners.service -n 200 # logs do último run agendado
docker exec -it adidas-db psql -U adidas -d adidas_runners -c 'SELECT count(*) FROM activities;'
```

## Rodar/simular local (máquina de dev)

Com Docker Desktop (emula arm64):
```bash
cd infrastructure/host
cp .env.example .env   # preencha
docker compose build bot && docker compose run --rm bot
```

## Notas
- **Isolamento:** nada compartilhado com a Florae além do hardware. Porta do Postgres
  só em `127.0.0.1:5433` (debug); o bot fala com o banco pela rede `adidas-net`.
- **Retry:** réplica fiel da state machine da AWS — o run agendado usa
  `run-with-retries.sh`, que tenta de novo espaçando **30m / 1h / 1h30** (até 4 tentativas)
  quando o bot sai com código != 0. Soma-se ao retry interno do app (3x por requisição +
  rotação de proxy). O run de validação (`deploy.sh --run` / `ansible -e run_now=true`)
  é single-shot (feedback rápido). `Persistent=true` recupera disparos perdidos.
- **Proxy:** `PROXY_ENABLED=false` por padrão (selenium-wire frágil em ARM).
- **Backup (opcional):** `docker exec adidas-db pg_dump -U adidas adidas_runners` num cron próprio.
- **Rollback:** o `infrastructure/template.yaml` (AWS SAM antigo) segue no repo só como referência.
