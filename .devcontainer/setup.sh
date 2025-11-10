#!/bin/bash
set -e

echo "🚀 Setting up SFPLiberate development environment..."

# Install Poetry if not already installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python dependencies
if [ -d "backend" ]; then
    echo "📚 Installing Python dependencies..."
    cd backend
    poetry config virtualenvs.create true
    poetry config virtualenvs.in-project true
    poetry install --no-interaction
    cd ..
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /data/sfplib
mkdir -p /data/backups

# Set up pre-commit hooks
if [ -f ".git/config" ]; then
    echo "🪝 Setting up git hooks..."
    git config --local core.hooksPath .githooks || true
fi

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Run task 'Start Home Assistant' to launch the supervisor"
echo "  2. Open http://localhost:7123 to access Home Assistant"
echo "  3. Install the SFPLiberate add-on from the Local Add-ons store"
echo ""
echo "📝 Available commands:"
echo "  - poetry run pytest (in backend/): Run tests"
echo "  - poetry run ruff check . (in backend/): Lint code"
echo "  - poetry run black . (in backend/): Format code"
