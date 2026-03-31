# BrahmaAI Production Deployment Guide

This guide covers deploying BrahmaAI to a Linux VPS (Ubuntu 22.04+) with:
- Nginx as reverse proxy
- Systemd for process management
- Let's Encrypt for SSL
- UFW firewall
- Optional: Caddy (simpler alternative to Nginx)

---

## 1. Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.12 python3.12-venv python3-pip \
  nodejs npm nginx certbot python3-certbot-nginx \
  git curl ufw fail2ban

# Install Node 20 (if apt version is old)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 2. Create Application User

```bash
sudo useradd -m -s /bin/bash brahmaai
sudo usermod -aG sudo brahmaai
su - brahmaai
```

---

## 3. Clone & Configure

```bash
cd /home/brahmaai
git clone https://github.com/yourname/brahmaai.git
cd brahmaai

# Configure environment
cp .env.example .env
nano .env  # Fill in API keys, change secrets
```

**Critical `.env` settings for production:**
```env
DEBUG=false
SECRET_KEY=<64-char random string>
JWT_SECRET=<64-char random string>
ALLOWED_ORIGINS=["https://yourdomain.com"]
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
FAISS_INDEX_PATH=/home/brahmaai/brahmaai/data/faiss_index
```

Generate secure secrets:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 4. Backend Setup

```bash
cd /home/brahmaai/brahmaai/backend

# Create virtualenv
python3.12 -m venv .venv
source .venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server

# Create data directory
mkdir -p /home/brahmaai/brahmaai/data

# Seed initial memories (optional)
cd /home/brahmaai/brahmaai
python seed.py
```

---

## 5. Frontend Build

```bash
cd /home/brahmaai/brahmaai/frontend

# Install and build
npm install
npm run build

# The output is in .next/
```

---

## 6. Systemd Service — Backend

```bash
sudo nano /etc/systemd/system/brahmaai-backend.service
```

```ini
[Unit]
Description=BrahmaAI Backend (FastAPI)
After=network.target
Wants=network.target

[Service]
Type=exec
User=brahmaai
Group=brahmaai
WorkingDirectory=/home/brahmaai/brahmaai
EnvironmentFile=/home/brahmaai/brahmaai/.env
ExecStart=/home/brahmaai/brahmaai/backend/.venv/bin/uvicorn \
    backend.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=brahmaai-backend

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/home/brahmaai/brahmaai/data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable brahmaai-backend
sudo systemctl start brahmaai-backend
sudo systemctl status brahmaai-backend
```

---

## 7. Systemd Service — Frontend

```bash
sudo nano /etc/systemd/system/brahmaai-frontend.service
```

```ini
[Unit]
Description=BrahmaAI Frontend (Next.js)
After=network.target brahmaai-backend.service
Wants=brahmaai-backend.service

[Service]
Type=exec
User=brahmaai
Group=brahmaai
WorkingDirectory=/home/brahmaai/brahmaai/frontend
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NEXT_PUBLIC_API_URL=https://yourdomain.com
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=brahmaai-frontend

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable brahmaai-frontend
sudo systemctl start brahmaai-frontend
```

---

## 8. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/brahmaai
```

```nginx
# Upstream servers
upstream brahmaai_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream brahmaai_frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL (managed by certbot)
    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # File upload limit
    client_max_body_size 25M;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # API routes → Backend
    location /api/ {
        proxy_pass         http://brahmaai_backend;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # SSE streaming — disable buffering
        proxy_buffering        off;
        proxy_cache            off;
        proxy_read_timeout     3600s;
        proxy_connect_timeout  60s;
        chunked_transfer_encoding on;
    }

    # All other routes → Frontend
    location / {
        proxy_pass         http://brahmaai_frontend;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Static assets — long cache
    location /_next/static/ {
        proxy_pass http://brahmaai_frontend;
        expires    365d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/brahmaai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 9. SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
# Certbot auto-configures SSL and sets up renewal cron
```

---

## 10. Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
sudo ufw status
```

---

## 11. Monitoring & Logs

```bash
# View backend logs
sudo journalctl -u brahmaai-backend -f

# View frontend logs
sudo journalctl -u brahmaai-frontend -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart brahmaai-backend brahmaai-frontend
```

---

## 12. Updates

```bash
cd /home/brahmaai/brahmaai
git pull origin main

# Backend
cd backend && source .venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart brahmaai-backend

# Frontend
cd ../frontend && npm install && npm run build
sudo systemctl restart brahmaai-frontend
```

---

## 13. Alternative: Docker Compose (Simplest)

If you prefer Docker:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker brahmaai

# Deploy
cd /home/brahmaai/brahmaai
cp .env.example .env && nano .env
docker-compose up -d --build

# Logs
docker-compose logs -f

# Update
git pull && docker-compose up -d --build
```

---

## 14. Health Checks

```bash
# Check API health
curl https://yourdomain.com/api/health

# Expected response:
# {"status":"ok","app":"BrahmaAI","version":"1.0.0","provider":"openai"}

# Check services
sudo systemctl status brahmaai-backend brahmaai-frontend nginx
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Backend not starting | Check `journalctl -u brahmaai-backend` for import errors |
| SSE streaming broken | Ensure nginx has `proxy_buffering off` for `/api/` |
| File uploads failing | Check `client_max_body_size` in nginx config |
| CORS errors | Verify `ALLOWED_ORIGINS` in `.env` matches your domain |
| Memory not persisting | Check `FAISS_INDEX_PATH` permissions |
| Out of memory | Reduce `MAX_ITERATIONS` and `LLM_MAX_TOKENS` in `.env` |
