#!/bin/bash

# ============================================
# 💾 Cake House — Local Database Backup
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

log "💾 Creating database backup..."

# PostgreSQL Backup (Docker)
docker compose exec -T db pg_dump -U postgres cake_house > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"
success "Backup created: ${BACKUP_FILE}.gz"

# Show size
SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
log "📊 Backup size: $SIZE"

# Keep only last 10 backups
log "🧹 Cleaning old backups (keeping last 10)..."
ls -t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm
success "Old backups cleaned"

echo ""