#!/bin/bash

echo "🚀 Setting up Sifting Tool..."

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt
cd ..

# Check if .env file exists
if [ ! -f backend/.env ]; then
    echo "⚠️  Creating .env file from template..."
    cp backend/env_example.txt backend/.env
    echo "📝 Please edit backend/.env and add your OPENAI_API_KEY"
fi

echo "✅ Setup complete!"
echo ""
echo "To start both servers:"
echo "  npm start"
echo ""
echo "Or start them separately:"
echo "  npm run frontend  (React on http://localhost:3003)"
echo "  npm run backend   (Flask on http://localhost:5000)"
