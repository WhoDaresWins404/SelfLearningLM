#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/WhoDaresWins404/SelfLearningLM.git"
INSTALL_DIR="/opt/selflearninglm"

echo "=== SelfLearningLM VM Setup ==="

# Install system deps
sudo apt-get update -y
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev git curl

# Clone repo
sudo git clone "$REPO_URL" "$INSTALL_DIR"
sudo chown -R "$USER:$USER" "$INSTALL_DIR"

# Python venv
cd "$INSTALL_DIR"
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# Frontend build
if command -v node &> /dev/null; then
    cd frontend
    npm install
    npm run build
    cd ..
fi

# Copy .env
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Systemd service
sudo cp deploy/selflearninglm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable selflearninglm.service
sudo systemctl start selflearninglm.service

echo "=== Setup complete ==="
echo "Service status:"
sudo systemctl status selflearninglm.service --no-pager
