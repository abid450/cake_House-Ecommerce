#!/bin/bash

# ============================================
# 🎯 Cake House — Development Helper
# ============================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

show_help() {
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  🍰 Cake House ERP — Development Helper"
    echo "════════════════════════════════════════════════════════"
    echo ""
    echo "  Usage: bash .scripts/dev.sh [command]"
    echo ""
    echo "  Commands:"
    echo ""
    echo "    🚀 start        Start all services"
    echo "    🛑 stop         Stop all services"
    echo "    🔄 restart      Restart all services"
    echo "    📝 logs         View logs"
    echo "    🐚 shell        Open Django shell"
    echo "    🧪 test         Run tests"
    echo "    🗄️  migrate      Run migrations"
    echo "    👤 superuser    Create superuser"
    echo "    💾 backup       Backup database"
    echo "    🌱 seed         Seed test data"
    echo "    🧹 clean        Clean Docker resources"
    echo "    🔄 reset-db     Reset database (DANGEROUS!)"
    echo "    📊 status       Show container status"
    echo "    ❓ help         Show this help"
    echo ""
}

case "${1:-help}" in
    start)      bash .scripts/start.sh ;;
    stop)       bash .scripts/stop.sh ;;
    restart)    bash .scripts/restart.sh ;;
    logs)       bash .scripts/logs.sh ;;
    shell)      bash .scripts/shell.sh ;;
    test)       bash .scripts/test.sh ;;
    migrate)    bash .scripts/migrate.sh ;;
    superuser)  bash .scripts/superuser.sh ;;
    backup)     bash .scripts/backup.sh ;;
    seed)       bash .scripts/seed-data.sh ;;
    clean)      bash .scripts/clean.sh ;;
    reset-db)   bash .scripts/reset-db.sh ;;
    status)     docker compose ps ;;
    help|*)     show_help ;;
esac