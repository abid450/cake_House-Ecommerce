#!/bin/bash

set -e

echo "🚀 Starting Cake House..."

# Wait for RabbitMQ
echo "⏳ Waiting for RabbitMQ..."
while ! nc -z $RABBITMQ_HOST $RABBITMQ_PORT; do
  sleep 0.1
done
echo "✅ RabbitMQ started"

# Wait for Redis
echo "⏳ Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 0.1
done
echo "✅ Redis started"

# Run migrations
echo "📦 Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (optional)
echo "👤 Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created')
else:
    print('ℹ️ Superuser already exists')
"

# Start server
echo "🌐 Starting Django server..."
exec "$@"