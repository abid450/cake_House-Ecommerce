#!/bin/bash

# ============================================
# 👤 Cake House — Create Superuser
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

echo ""
log "👤 Creating superuser..."
echo ""

docker compose exec web python manage.py createsuperuser

success "Superuser created!"
echo ""