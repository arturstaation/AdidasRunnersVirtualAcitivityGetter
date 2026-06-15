#!/usr/bin/env bash
# Spike arm64 — roda NA VM Oracle (build nativo arm64, sem emulação).
# Valida, em estágios, do mais barato/isolado ao mais completo. Pare no primeiro
# que falhar: ele aponta exatamente onde está o problema.
#
#   chmod +x infrastructure/smoke/run-smoke.sh
#   ./infrastructure/smoke/run-smoke.sh          # estágios 0..2 (sem DB/Telegram)
#   FULL=1 ./infrastructure/smoke/run-smoke.sh   # + estágio 3 (app real)
#
# Estágio 3 exige um .env com TOKEN/CHAT_ID e o Postgres dedicado do stack
# (adidas-db na rede adidas-net). Em geral nem precisa: prefira o fluxo oficial
# `infrastructure/host/deploy.sh --run`. Os estágios 0..2 já derrubam o risco do ARM.
set -euo pipefail

IMAGE="adidas-runners:smoke"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> Estágio 0: build arm64 nativo ($(uname -m))"
docker build -t "$IMAGE" .

echo ""
echo "==> Estágio 1: versões do Chromium/chromedriver dentro da imagem"
docker run --rm --entrypoint /bin/sh "$IMAGE" -c \
  'echo -n "chromium: "; "$CHROME_BIN" --version; \
   echo -n "driver:   "; "$CHROMEDRIVER_PATH" --version; \
   echo -n "arch:     "; uname -m'

echo ""
echo "==> Estágio 2: Selenium headless batendo na API do Adidas (isolado)"
# Monta o smoke por cima da imagem e roda. --shm-size evita crash do Chrome.
docker run --rm --shm-size=1g \
  -v "$ROOT/infrastructure/smoke/smoke_selenium.py:/app/src/smoke_selenium.py:ro" \
  --entrypoint python "$IMAGE" smoke_selenium.py

if [ "${FULL:-0}" = "1" ]; then
  echo ""
  echo "==> Estágio 3: app completo (DB + Telegram) usando .env"
  if [ ! -f .env ]; then
    echo "FULL=1 mas não há .env na raiz. Crie com TOKEN/CHAT_ID/PG_*." >&2
    exit 2
  fi
  # Anexe à rede do stack (adidas-net) para alcançar o adidas-db:
  #   docker run ... --network adidas-net ...   (PG_HOST=adidas-db no .env)
  docker run --rm --shm-size=1g --env-file .env "$IMAGE"
fi

echo ""
echo "✅ Smoke-test concluído (estágios até $([ "${FULL:-0}" = "1" ] && echo 3 || echo 2))."
