#!/usr/bin/env bash
set -euo pipefail

SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="$(id -un)"
PORT="${PORT:-8080}"

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv python3-pip sqlite3 curl

if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 1G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

cd "$SERVER_DIR"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f /etc/techprice.env ]; then
  sudo tee /etc/techprice.env >/dev/null <<ENV
JWT_SECRET=$(openssl rand -hex 32)
PORT=$PORT
ENV
  sudo chmod 600 /etc/techprice.env
fi

sudo tee /etc/systemd/system/techprice.service >/dev/null <<UNIT
[Unit]
Description=TechPrice API
After=network-online.target
Wants=network-online.target

[Service]
User=$RUN_USER
WorkingDirectory=$SERVER_DIR
EnvironmentFile=/etc/techprice.env
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8
ExecStart=$SERVER_DIR/.venv/bin/python -m app.main
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable techprice >/dev/null
sudo systemctl restart techprice

for _ in $(seq 1 20); do
  if curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1; then
    PUBLIC_IP="$(curl -fsS --max-time 5 https://api.ipify.org || echo '<IP машины>')"
    echo
    echo "Сервер запущен: http://$PUBLIC_IP:$PORT/health"
    echo "Журнал: journalctl -u techprice -f"
    exit 0
  fi
  sleep 1
done

echo "Сервер не ответил. Журнал:"
sudo journalctl -u techprice -n 50 --no-pager
exit 1
