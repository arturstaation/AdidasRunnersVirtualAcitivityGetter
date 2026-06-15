#!/usr/bin/env bash
# Roda NA VM (host). Build arm64 NATIVO + sobe o Postgres dedicado + (re)instala o
# systemd timer. Com --run, dispara uma execução imediata e mostra os logs.
# É chamado pelo CI via SSH, mas também serve pra deploy manual.
#
#   ./deploy.sh           # build + db + timer
#   ./deploy.sh --run     # idem + 1 execução agora
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"   # .../infrastructure/host
cd "$HERE"

if [ ! -f .env ]; then
  echo "ERRO: $HERE/.env não existe. Crie a partir de .env.example (fica só na VM)." >&2
  exit 1
fi

echo "==> Build do bot (arm64 nativo: $(uname -m))"
docker compose build bot

echo "==> Subindo Postgres dedicado (adidas-db)"
docker compose up -d db

echo "==> (Re)instalando systemd timer (a cada 6h)"
TMP_SVC="$(mktemp)"
sed "s#__WORKDIR__#${HERE}#g" systemd/adidas-runners.service > "$TMP_SVC"
sudo install -m 0644 "$TMP_SVC" /etc/systemd/system/adidas-runners.service
sudo install -m 0644 systemd/adidas-runners.timer /etc/systemd/system/adidas-runners.timer
rm -f "$TMP_SVC"
sudo systemctl daemon-reload
sudo systemctl enable --now adidas-runners.timer
echo "    timer ativo. Próximos disparos:"
systemctl list-timers adidas-runners.timer --no-pager 2>/dev/null | head -2 || true

if [ "${1:-}" = "--run" ]; then
  echo ""
  echo "==> Execução imediata"
  # Roda direto (não via systemd) pra capturar o exit code e os logs no pipeline.
  if docker compose run --rm bot; then
    echo "✅ Run concluído com sucesso."
  else
    echo "❌ Run falhou (veja os logs acima)." >&2
    exit 1
  fi
fi

echo "✅ Deploy concluído."
