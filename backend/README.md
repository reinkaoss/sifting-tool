# Sifting Tool Backend

Simple Flask API for analyzing CSV job applications with OpenAI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

3. Run the server:
```bash
python app.py
```

The server will run on http://localhost:5000

## API Endpoints

- `GET /health` - Health check
- `POST /analyze` - Analyze CSV data

### Analyze Request Body:
```json
{
  "client": "Client Name",
  "jobDescription": "Job description text",
  "csvData": [array of CSV rows],
  "userCount": 33
}
```

### Analyze Response:
```json
{
  "success": true,
  "analysis": "AI analysis text",
  "userCount": 33,
  "client": "Client Name"
}
```
