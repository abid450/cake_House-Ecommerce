#!/bin/bash

# ============================================
# 🧪 Cake House — Run Tests
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo ""
echo "🧪 Running Tests..."
echo ""

log "Running Django tests..."
if docker compose exec -T web python manage.py test --verbosity=2; then
    success "All tests passed!"
else
    error "Some tests failed!"
fi

echo ""