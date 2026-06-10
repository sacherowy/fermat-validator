# Production Deployment Guide

This guide covers deploying FerMat Validator to a local Intel NUC server with
Docker Compose and a Cloudflare Tunnel.

## Architecture Overview

```
Internet
    │
    ▼
Cloudflare Tunnel (https://fermat-validator.pl)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  NUC server                                         │
│                                                     │
│  ┌─────────────────┐                               │
│  │ Nginx           │ 127.0.0.1:3100                │
│  │ (container)     │ WebSocket → API, rest → FE    │
│  └────────┬────────┘                               │
│           │                                         │
│           ├──────────────────┐                     │
│           ▼                  ▼                     │
│  ┌────────────────┐  ┌────────────────┐           │
│  │ Frontend       │  │ API            │           │
│  │ (Next.js)      │  │ (FastAPI)      │           │
│  │ internal       │  │ 127.0.0.1:8100 │           │
│  └────────────────┘  └───────┬────────┘           │
│                              │                     │
│                              ▼                     │
│                      ┌────────────────┐           │
│                      │ PostgreSQL     │           │
│                      │ (internal)     │           │
│                      └────────────────┘           │
│                                                     │
│  Data: ~/fermat-validator/data/                    │
│    ├── postgres/    (database files)               │
│    └── uploads/     (user images)                  │
└─────────────────────────────────────────────────────┘
```

**Domain**: https://fermat-validator.pl (Cloudflare Tunnel)

All services are defined in `docker-compose.prod.yml`. The Nginx container
(`nginx.prod.conf`) routes `/ws/` traffic to the API and everything else to the
frontend; the Cloudflare Tunnel on the server points at `localhost:3100`.

## Prerequisites

- Server with Docker and the Docker Compose plugin installed
- SSH access to the server
- Cloudflare account with the domain and a tunnel configured
- Google OAuth credentials configured for the domain
- GitHub Container Registry (ghcr.io) access for pulling images

## Server Setup (One-Time)

### 1. Clone and Configure

```bash
# On the server
git clone https://github.com/sacherowy/fermat-validator.git
cd fermat-validator

# Create production env file
cp .env.prod.example .env.prod

# Edit with production values
nano .env.prod
```

Required `.env.prod` variables:
```bash
POSTGRES_PASSWORD=<secure-password>
SESSION_SECRET_KEY=<generate-with: openssl rand -hex 32>
GOOGLE_CLIENT_ID=<from-google-console>
GOOGLE_CLIENT_SECRET=<from-google-console>
GEMINI_API_KEY=<from-google-ai-studio>
ALLOWED_EMAILS=user1@gmail.com,user2@gmail.com
FRONTEND_URL=https://fermat-validator.pl
```

### 2. Configure the Cloudflare Tunnel

Install `cloudflared` on the server and route the public hostname
(`fermat-validator.pl`) to `http://localhost:3100` (the Nginx container).
See the [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
for details.

### 3. Start Services

```bash
cd ~/fermat-validator
docker compose -f docker-compose.prod.yml --env-file .env.prod pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Deployment (Updates)

Images are built locally and pushed to GitHub Container Registry (`ghcr.io`),
then pulled on the server.

### One-Time Setup (Local Machine)

```bash
# 1. Create GitHub Personal Access Token (PAT)
#    Go to https://github.com/settings/tokens
#    Create token with 'write:packages' scope

# 2. Login to GitHub Container Registry
echo YOUR_PAT | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### Deploy from Local Machine

```bash
# Build images locally and push to registry
./build-and-push.sh

# Deploy to server (pulls images from ghcr.io)
./deploy.sh

# Or both in one command
./build-and-push.sh && ./deploy.sh
```

### Deploy Script Options

```bash
./deploy.sh                  # Pull latest and restart all services
./deploy.sh --api            # Deploy only API
./deploy.sh --frontend       # Deploy only frontend
./deploy.sh --logs api       # View API logs
./deploy.sh --status         # Check container status
./deploy.sh --ssh            # SSH into the server
```

### Build Script Options

```bash
./build-and-push.sh                  # Build and push both images
./build-and-push.sh --api            # Build and push API only
./build-and-push.sh --frontend       # Build and push frontend only
./build-and-push.sh --tag v1.0.0     # Use specific tag
./build-and-push.sh --no-push        # Build only, don't push
```

## Operations

### View Logs

```bash
# API logs (most useful for debugging)
docker logs fermat-api --tail=100 -f

# Frontend logs
docker logs fermat-frontend --tail=50 -f

# Database logs
docker logs fermat-db --tail=50

# Nginx logs
docker logs fermat-nginx --tail=50
```

### Service Management

```bash
# Check status
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

# Restart services
docker compose -f docker-compose.prod.yml --env-file .env.prod restart api
docker compose -f docker-compose.prod.yml --env-file .env.prod restart frontend

# Stop all
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# Stop and remove volumes (CAUTION: deletes data)
docker compose -f docker-compose.prod.yml --env-file .env.prod down -v
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it fermat-db psql -U fermat -d fermat

# Useful queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM submissions;
SELECT * FROM submissions ORDER BY created_at DESC LIMIT 10;
```

### Backup

```bash
# Backup database
docker exec fermat-db pg_dump -U fermat fermat > backup_$(date +%Y%m%d).sql

# Backup uploads
tar -czf uploads_$(date +%Y%m%d).tar.gz data/uploads/
```

## Data Storage

All persistent data is stored in `~/fermat-validator/data/` via bind mounts:

```
~/fermat-validator/data/
├── postgres/                    # PostgreSQL database files
└── uploads/                     # User-submitted images
    └── {user_id}/
        └── {year}/
            └── {etap}/
                └── {task_num}/
                    └── *.jpg
```

## Docker Compose Services

Defined in `docker-compose.prod.yml`:

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| db | fermat-db | internal | PostgreSQL 16, only accessible within Docker network |
| api | fermat-api | 127.0.0.1:8100 | FastAPI backend |
| frontend | fermat-frontend | internal | Next.js standalone server, accessed via Nginx |
| nginx | fermat-nginx | 127.0.0.1:3100 | Reverse proxy: WebSocket → API, rest → frontend |

## Troubleshooting

### Container won't start

```bash
# Check container logs
docker logs fermat-api

# Common issues:
# - Missing environment variables in .env.prod
# - Database not ready (check fermat-db health)
# - Port already in use
```

### WebSocket not working

- Ensure `nginx.prod.conf` includes WebSocket upgrade headers (it does by default)
- Check API logs for session decode errors
- Verify `FRONTEND_URL` matches the actual domain

### Site not reachable

```bash
# Check the tunnel is running on the server
systemctl status cloudflared

# Check Nginx responds locally
curl -I http://127.0.0.1:3100
```

### Database connection issues

```bash
# Check if db container is healthy
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

# Restart database
docker compose -f docker-compose.prod.yml --env-file .env.prod restart db
```

## Security Notes

- Nginx and the API bind to `127.0.0.1` only; public traffic enters exclusively
  through the Cloudflare Tunnel
- PostgreSQL is not exposed to the host, only accessible within the Docker network
- Containers run with `no-new-privileges` and all capabilities dropped
- Session cookies are HttpOnly and Secure
- Use strong passwords in `.env.prod`
