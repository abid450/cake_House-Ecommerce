#!/bin/bash

# ============================================
# 🐚 Cake House — Django Shell
# ============================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐚 Opening Django Shell...${NC}"
echo ""

docker compose exec web python manage.py shell