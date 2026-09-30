#!/bin/bash

# ============================================
# 🚀 Cake House ERP — Deployment Script
# ============================================

set -euo pipefail

# ============================================
# 📌 Configuration
# ============================================
ENVIRONMENT="${1:-staging}"
PROJECT_DIR="/e/Cake_House/cooking"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$PROJECT_DIR/logs/deploy.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ============================================
# 🎨 Colors
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# 📝 Logging
# ============================================
log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"; exit 1; }

# ============================================
# 🔍 Pre-flight Checks
# ============================================
preflight_checks() {
    log "🔍 Running pre-flight checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed!"
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed!"
    fi
    
    # Check .env
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        error ".env file not found!"
    fi
    
    success "All pre-flight checks passed"
}

# ============================================
# 💾 Database Backup
# ============================================
backup_database() {
    log "💾 Creating database backup..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/db_backup_${ENVIRONMENT}_${TIMESTAMP}.sql"
    
    cd "$PROJECT_DIR"
    
    if docker compose exec -T db pg_dump -U postgres cake_house > "$BACKUP_FILE" 2>/dev/null; then
        gzip "$BACKUP_FILE"
        success "Database backup created: ${BACKUP_FILE}.gz"
        
        # Keep last 7 backups
        ls -t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm
        log "🗑️  Old backups cleaned up"
    else
        warning "Database backup failed (DB may not be running)"
    fi
}

# ============================================
# 🐳 Build & Deploy
# ============================================
deploy_containers() {
    log "🐳 Building Docker containers..."
    
    cd "$PROJECT_DIR"
    
    # Build
    docker compose build
    success "Docker images built"
    
    # Restart
    log "🚀 Restarting containers..."
    docker compose up -d
    success "Containers deployed"
    
    # Wait
    log "⏳ Waiting for services..."
    sleep 10
}

# ============================================
# 🗄️ Run Migrations
# ============================================
run_migrations() {
    log "🗄️  Running migrations..."
    
    cd "$PROJECT_DIR"
    
    if docker compose exec -T web python manage.py migrate --noinput; then
        success "Migrations applied"
    else
        error "Migration failed"
    fi
}

# ============================================
# 📁 Collect Static
# ============================================
collect_static() {
    log "📁 Collecting static files..."
    
    cd "$PROJECT_DIR"
    
    if docker compose exec -T web python manage.py collectstatic --noinput; then
        success "Static files collected"
    else
        warning "Static collection failed"
    fi
}

# ============================================
# 🏥 Health Check
# ============================================
health_check() {
    log "🏥 Running health check..."
    
    sleep 5
    
    # Check container
    if ! docker compose ps web | grep -q "Up"; then
        error "Web container is not running"
    fi
    
    # Check HTTP
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "000")
    
    if [[ "$HTTP_STATUS" == "200" ]] || [[ "$HTTP_STATUS" == "302" ]]; then
        success "Health check passed (HTTP $HTTP_STATUS)"
    else
        warning "Health check returned HTTP $HTTP_STATUS"
    fi
}

# ============================================
# 📊 Summary
# ============================================
show_summary() {
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  🎉 Deployment Summary"
    echo "════════════════════════════════════════════════════════"
    echo "  Environment:   $ENVIRONMENT"
    echo "  Timestamp:     $(date +'%Y-%m-%d %H:%M:%S')"
    echo "  Duration:      ${DEPLOY_DURATION}s"
    echo "════════════════════════════════════════════════════════"
    echo ""
    success "Deployment completed! 🚀"
}

# ============================================
# 🎯 Main
# ============================================
main() {
    START_TIME=$(date +%s)
    
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  🚀 Cake House ERP — Deployment"
    echo "════════════════════════════════════════════════════════"
    echo "  Environment: $ENVIRONMENT"
    echo "════════════════════════════════════════════════════════"
    echo ""
    
    preflight_checks
    backup_database
    deploy_containers
    run_migrations
    collect_static
    health_check
    
    END_TIME=$(date +%s)
    DEPLOY_DURATION=$((END_TIME - START_TIME))
    
    show_summary
}

main "$@"