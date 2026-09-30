#!/bin/bash

# ============================================
# ⚠️ Cake House — Reset Database (DANGEROUS!)
# ============================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${RED}⚠️  WARNING: This will DELETE all data!${NC}"
echo ""
read -p "Are you sure? Type 'YES' to continue: " CONFIRM

if [[ "$CONFIRM" != "YES" ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🔄 Resetting database..."

# Stop containers
docker compose down

# Remove database volume
docker volume rm cooking_postgres_data 2>/dev/null || true

# Start fresh
docker compose up -d

# Wait
sleep 10

# Run migrations
docker compose exec -T web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

echo -e "${GREEN}✅ Database reset complete!${NC}"
echo ""