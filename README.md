# Sifting Tool

A web application for analyzing job application CSV files using AI.

## Quick Start

### Option 1: One-Command Setup
```bash
./setup.sh
npm start
```

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   # Frontend
   npm install
   
   # Backend
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

2. **Set up environment:**
   ```bash
   # Copy environment template
   cp backend/env_example.txt backend/.env
   
   # Edit backend/.env and add your OpenAI API key
   OPENAI_API_KEY=your_key_here
   ```

3. **Start both servers:**
   ```bash
   npm start
   ```

## What Runs

- **Frontend**: React app on http://localhost:3003
- **Backend**: Flask API on http://localhost:5000

## Usage

1. Upload a CSV file with job applications
2. Select a client from the dropdown
3. Enter job description
4. Click "Process File" to get AI analysis

## Individual Commands

- `npm start` - Run both frontend and backend
- `npm run frontend` - Run only React frontend (port 3003)
- `npm run backend` - Run only Flask backend

## Google Sheets Integration

The application can automatically analyze job applications from Google Sheets:

- **Read** applications from your Google Sheet
- **Analyze** using AI with detailed scoring
- **Write** results to a new "AI Analysis" tab with scores and reasoning

### Quick Start

1. Set up Google Cloud service account (see `GOOGLE_SHEETS_SETUP.md`)
2. Share your spreadsheet with the service account
3. Run the analyzer:
   ```bash
   cd backend
   python3 sheets_processor.py
   ```

For detailed setup instructions, see `GOOGLE_SHEETS_SETUP.md`
