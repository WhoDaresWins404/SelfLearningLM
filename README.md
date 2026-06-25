# SelfLearningLM

Intelligent web crawler with evasion engine and structured data extraction pipeline.

## Architecture

- **Crawler** — Scrapy-based, configurable evasion state machine (WAF, CAPTCHA, rate limits, fingerprinting, honeypots)
- **Processor** — Rule-based content analysis, per-schema extraction, dedup, scoring, refinement
- **Storage** — Filesystem data lake (raw HTML) + SQLite (structured records, indexes, metadata)
- **Web UI** — Vue 3 SPA served by FastAPI, featuring visual container schema builder
- **Deployment** — Single Python process via uvicorn, systemd-managed on Ubuntu 26.04 LTS

## Quick Start

```bash
# Clone
git clone https://github.com/WhoDaresWins404/SelfLearningLM.git
cd SelfLearningLM

# Backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

# Frontend
cd frontend
npm install
npm run build
cd ..

# Run
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## CLI Usage

```bash
# Start web server
selflearninglm serve --host 0.0.0.0 --port 8000

# Run a crawl
selflearninglm crawl --domain example.com --url https://example.com

# Process scraped data
selflearninglm process --domain example.com

# Seed container schemas
selflearninglm seed
```

## Pre-Seeded Container Schemas

1. **Detailed Technical Documentation** — Code snippets, function params, headings
2. **Forum Posts and Discussions** — Threads, author, timestamps, code blocks
3. **Malformed or Obfuscated Code Snippets** — eval(), base64, hex-encoded scripts
4. **Dynamic Content (AJAX Calls)** — API endpoints, fetch/XHR payloads
5. **Hidden Data (CSS/JS Obfuscation)** — display:none traps, keyframe tricks, base64 data

All schemas are fully editable via the web UI form builder.

## VM Deployment

```bash
chmod +x deploy/setup_vm.sh
sudo ./deploy/setup_vm.sh
```

## License

MIT
