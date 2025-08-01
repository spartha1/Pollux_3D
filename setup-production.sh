#!/bin/bash

# Production Setup Script for Pollux 3D Analysis System
# This script configures the Python environment for production deployment

echo "🚀 Setting up Pollux 3D for Production..."

# Detect Python environment
detect_python_env() {
    echo "🔍 Detecting Python environment..."
    
    # Check for conda
    if command -v conda &> /dev/null; then
        echo "✅ Conda found"
        
        # Check if pollux-preview-env exists
        if conda env list | grep -q "pollux-preview-env"; then
            echo "✅ pollux-preview-env environment found"
            CONDA_ENV_PATH=$(conda env list | grep pollux-preview-env | awk '{print $2}')
            PYTHON_PATH="$CONDA_ENV_PATH/bin/python"
            
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                PYTHON_PATH="$CONDA_ENV_PATH/python.exe"
            fi
            
            return 0
        else
            echo "❌ pollux-preview-env not found. Creating environment..."
            conda create -n pollux-preview-env python=3.9 -y
            conda activate pollux-preview-env
            pip install -r requirements.txt
            return 0
        fi
    fi
    
    # Check for system Python
    if command -v python3 &> /dev/null; then
        echo "✅ System Python3 found"
        PYTHON_PATH=$(which python3)
        return 0
    elif command -v python &> /dev/null; then
        echo "✅ System Python found"
        PYTHON_PATH=$(which python)
        return 0
    fi
    
    echo "❌ No Python installation found!"
    return 1
}

# Update .env file for production
setup_env_file() {
    echo "⚙️ Configuring environment variables..."
    
    if [[ -f .env ]]; then
        # Remove old hardcoded paths
        sed -i '/CONDA_ROOT=C:\\Users\\/d' .env
        sed -i '/PYTHON_EXECUTABLE.*Users/d' .env
        
        # Add detected Python path if available
        if [[ -n "$PYTHON_PATH" ]]; then
            echo "PYTHON_EXECUTABLE=$PYTHON_PATH" >> .env
            echo "✅ Python path configured: $PYTHON_PATH"
        fi
        
        # Set production environment
        sed -i 's/APP_ENV=local/APP_ENV=production/' .env
        sed -i 's/APP_DEBUG=true/APP_DEBUG=false/' .env
        
        echo "✅ Environment file configured for production"
    else
        echo "❌ .env file not found! Please copy .env.example to .env first."
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    # PHP dependencies
    if command -v composer &> /dev/null; then
        composer install --optimize-autoloader --no-dev
        echo "✅ PHP dependencies installed"
    else
        echo "❌ Composer not found!"
        return 1
    fi
    
    # Python dependencies
    if [[ -f requirements.txt ]]; then
        if [[ -n "$PYTHON_PATH" ]]; then
            $PYTHON_PATH -m pip install -r requirements.txt
            echo "✅ Python dependencies installed"
        fi
    fi
    
    # Node.js dependencies
    if command -v npm &> /dev/null; then
        npm ci --production
        npm run build
        echo "✅ Frontend built for production"
    fi
}

# Optimize Laravel
optimize_laravel() {
    echo "⚡ Optimizing Laravel for production..."
    
    php artisan config:cache
    php artisan route:cache
    php artisan view:cache
    php artisan event:cache
    
    echo "✅ Laravel optimized"
}

# Set proper permissions
set_permissions() {
    echo "🔐 Setting proper permissions..."
    
    # Set storage and cache permissions
    chmod -R 775 storage bootstrap/cache
    
    # Set ownership (adjust for your server setup)
    # chown -R www-data:www-data storage bootstrap/cache
    
    echo "✅ Permissions configured"
}

# Main execution
main() {
    if detect_python_env; then
        setup_env_file
        install_dependencies
        optimize_laravel
        set_permissions
        
        echo "🎉 Production setup completed successfully!"
        echo "📝 Python path: ${PYTHON_PATH:-'Auto-detect will be used'}"
        echo "🚀 Your application is ready for production deployment."
    else
        echo "❌ Production setup failed due to Python environment issues."
        exit 1
    fi
}

# Run main function
main "$@"
