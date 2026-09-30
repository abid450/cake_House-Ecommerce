#!/bin/bash

# ============================================
# 🛑 Cake House — Stop Development Environment
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

echo ""
echo "🛑 Stopping Cake House Development Environment..."
echo ""

log "Stopping containers..."
docker compose down

success "All containers stopped!"
echo ""