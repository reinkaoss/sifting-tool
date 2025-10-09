import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import Flask app - Vercel will use 'app' as the WSGI application
from app import app

