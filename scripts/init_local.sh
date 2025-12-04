#!/bin/bash
set -e

# Enterprise MCP Local Development Setup Script

echo "🚀 Setting up Enterprise MCP local development environment..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }

echo "✅ Prerequisites check passed"

# Create virtual environment for Python
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate || . venv/Scripts/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Azure resource values"
fi

# Install frontend dependencies
if [ -d "web" ]; then
    echo "📦 Installing frontend dependencies..."
    cd web
    npm install
    cd ..
fi

# Start Docker Compose services
echo "🐳 Starting Docker Compose services (Redis)..."
docker-compose up -d redis

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
sleep 5

echo ""
echo "✅ Local development environment setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Edit .env file with your Azure resource URLs (Key Vault, Storage, etc.)"
echo "  2. Start the backend: uvicorn src.app.main:app --reload"
echo "  3. Start the frontend: cd web && npm run dev"
echo "  4. Open http://localhost:5173 in your browser"
echo ""
echo "🔧 Useful commands:"
echo "  - Run all services: docker-compose up"
echo "  - Stop services: docker-compose down"
echo "  - View logs: docker-compose logs -f"
echo "  - Backend tests: pytest"
echo ""
