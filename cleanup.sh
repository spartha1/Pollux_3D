#!/bin/bash

echo "🧹 Limpiando procesos existentes..."

# Matar procesos específicos
pkill -f "php artisan serve" 2>/dev/null || true
pkill -f "php artisan queue" 2>/dev/null || true
pkill -f "preview_server.py" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# Liberar puertos específicos
lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
lsof -ti:8052 | xargs -r kill -9 2>/dev/null || true
lsof -ti:5173 | xargs -r kill -9 2>/dev/null || true
lsof -ti:5174 | xargs -r kill -9 2>/dev/null || true
lsof -ti:5175 | xargs -r kill -9 2>/dev/null || true

# Esperar un momento
sleep 2

echo "✅ Limpieza completada"
