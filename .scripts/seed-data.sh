#!/bin/bash

# ============================================
# 🌱 Cake House — Seed Test Data
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

echo ""
log "🌱 Seeding test data..."
echo ""

docker compose exec -T web python manage.py shell << 'EOF'
from category.models import Category, DessertType
from products.models import Product
from decimal import Decimal

# Create Categories
categories = ['Cake', 'Bread', 'Pastry', 'Cookie', 'Donut']
for name in categories:
    cat, created = Category.objects.get_or_create(name=name)
    if created:
        print(f"✅ Category created: {name}")

# Create Dessert Types
dessert_types = ['Cupcake', 'Cheesecake', 'Brownie', 'Muffin']
for name in dessert_types:
    dt, created = DessertType.objects.get_or_create(name=name)
    if created:
        print(f"✅ Dessert Type created: {name}")

# Create Sample Products
cake_cat = Category.objects.get(name='Cake')
products = [
    {'name': 'Chocolate Cake', 'price': 800, 'quantity': 20},
    {'name': 'Vanilla Cake', 'price': 700, 'quantity': 15},
    {'name': 'Red Velvet Cake', 'price': 900, 'quantity': 10},
    {'name': 'Strawberry Cake', 'price': 850, 'quantity': 12},
]
for p in products:
    product, created = Product.objects.get_or_create(
        name=p['name'],
        defaults={
            'category': cake_cat,
            'price': Decimal(str(p['price'])),
            'quantity': p['quantity'],
            'min_stock_level': 5,
            'is_active': True,
        }
    )
    if created:
        print(f"✅ Product created: {p['name']}")

print("\n🎉 Seeding complete!")
EOF

success "Test data seeded!"
echo ""