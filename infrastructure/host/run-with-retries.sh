#!/usr/bin/env bash
# Replica a AWS Step Functions: roda o bot e, em caso de FALHA, tenta de novo
# espaçando 30m / 1h / 1h30 — idêntico a Wait30m / Wait1h / Wait1h30min.
# Até 4 tentativas (RunJob + TryAgain1/2/3); depois desiste (= estado Failed).
#
# "Falha" = o bot sair com código != 0 (main.py faz sys.exit(1) quando hasError).
# Usado pelo systemd timer (run agendado). O run de validação (deploy.sh --run /
# ansible run_now) NÃO usa retries — é single-shot pra feedback rápido.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

# Esperas entre tentativas (segundos): 30m, 1h, 1h30 — iguais à state machine.
WAITS=(1800 3600 5400)

attempt=0
while :; do
  attempt=$((attempt + 1))
  echo "==> Tentativa ${attempt}: docker compose run --rm bot"
  if docker compose run --rm bot; then
    echo "✅ Run OK na tentativa ${attempt}."
    exit 0
  fi
  echo "❌ Run falhou na tentativa ${attempt}."

  idx=$((attempt - 1))
  if [ "${idx}" -ge "${#WAITS[@]}" ]; then
    echo "Todas as ${attempt} tentativas falharam. Desistindo (Failed)." >&2
    exit 1
  fi

  w="${WAITS[$idx]}"
  echo "Aguardando ${w}s antes da próxima tentativa..."
  sleep "${w}"
done
