#!/bin/bash

# ============================================
# 🚀 Cake House — Start Development Environment
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo ""
echo "════════════════════════════════════════════════════════"
echo "  🚀 Cake House ERP — Starting Development"
echo "════════════════════════════════════════════════════════"
echo ""

# 1. Check Docker
log "🐳 Checking Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker is not installed!"
fi
success "Docker is installed"

# 2. Check if .env exists
if [[ ! -f ".env" ]]; then
    warn ".env file not found. Creating from .env.example..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        success ".env file created. Please edit it with your values."
    else
        error ".env.example not found!"
    fi
fi

# 3. Build images
log "🔨 Building Docker images..."
docker compose build
success "Images built"

# 4. Start services
log "🚀 Starting services..."
docker compose up -d
success "Services started"

# 5. Wait for services
log "⏳ Waiting for services to be healthy..."
sleep 10

# 6. Run migrations
log "🗄️  Running migrations..."
docker compose exec -T web python manage.py migrate --noinput
success "Migrations applied"

# 7. Collect static files
log "📁 Collecting static files..."
docker compose exec -T web python manage.py collectstatic --noinput
success "Static files collected"

# 8. Show status
echo ""
log "📊 Container Status:"
docker compose ps

echo ""
echo "════════════════════════════════════════════════════════"
echo "  🎉 Development Environment is Ready!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "  🌐 Application:  http://localhost:8000"
echo "  🔧 Admin Panel:  http://localhost:8000/admin/"
echo "  📊 Dashboard:    http://localhost:8000/dashboard/"
echo "  🌸 Flower:       http://localhost:5555"
echo "  🐰 RabbitMQ:     http://localhost:15672"
echo ""
echo "  📝 To view logs:   bash .scripts/logs.sh"
echo "  🛑 To stop:        bash .scripts/stop.sh"
echo ""