#!/bin/bash

# ============================================
# 🗄️ Cake House — Database Migration
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo ""
log "🗄️  Creating migrations..."
docker compose exec -T web python manage.py makemigrations
success "Migrations created"

log "🔄 Applying migrations..."
docker compose exec -T web python manage.py migrate
success "Migrations applied"

echo ""