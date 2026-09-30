#!/bin/bash

# ============================================
# 📝 Cake House — View Logs
# ============================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "📝 Viewing Logs..."
echo ""
echo "Options:"
echo "  1) All services"
echo "  2) Django (web)"
echo "  3) Celery Worker"
echo "  4) Celery Beat"
echo "  5) PostgreSQL (db)"
echo "  6) Redis"
echo "  7) RabbitMQ"
echo ""
read -p "Choose (1-7): " CHOICE

case $CHOICE in
    1) docker compose logs -f ;;
    2) docker compose logs -f web ;;
    3) docker compose logs -f celery_worker ;;
    4) docker compose logs -f celery_beat ;;
    5) docker compose logs -f db ;;
    6) docker compose logs -f redis ;;
    7) docker compose logs -f rabbitmq ;;
    *) echo "Invalid choice" ;;
esac