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
export OUTGOING_WEBHOOK_URL=https://your-webhook-url.com/endpoint  # Optional
```

Or create a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
OUTGOING_WEBHOOK_URL=https://your-webhook-url.com/endpoint
```

3. Run the server:
```bash
python app.py
```

The server will run on http://localhost:5000

## API Endpoints

- `GET /health` - Health check
- `POST /analyze` - Analyze CSV data (used by frontend)
- `POST /webhook/submit` - Incoming webhook for external submissions

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

## Webhook Integration

### Incoming Webhook: POST /webhook/submit

This endpoint allows external systems to submit applications for analysis. The system will:
1. Receive and validate the submission
2. Analyze applications using OpenAI
3. Forward results to the configured outgoing webhook (if set)

#### Request Format:
```json
{
  "client": "EDF Trading - Graduate Scheme",
  "jobDescription": "Description of the role...",
  "supportingReferences": "Optional additional context",
  "applications": [
    {
      "User": "1",
      "Question 1": "Why do you want this role?",
      "Question 2": "What are your strengths?",
      "Question 3": "Describe a challenge..."
    },
    {
      "User": "2",
      "Question 1": "...",
      "Question 2": "...",
      "Question 3": "..."
    }
  ]
}
```

#### Response Format:
```json
{
  "success": true,
  "analysis": "Full AI analysis with scores...",
  "userCount": 2,
  "client": "EDF Trading - Graduate Scheme",
  "webhookStatus": {
    "sent": true,
    "status_code": 200,
    "url": "https://your-webhook-url.com/endpoint"
  }
}
```

### Outgoing Webhook Payload

The outgoing webhook receives the complete analysis package:
```json
{
  "client": "EDF Trading - Graduate Scheme",
  "jobDescription": "Description of the role...",
  "userCount": 2,
  "applications": [...original application data...],
  "analysis": "1. **User 1 - Overall Score 13/15 - Q1: Yes Q2: Yes Q3: Yes Q4: 4* Q5: Yes Q6: 4* Q7: 5* - Strong candidate...**\n\n2. **User 2 - Overall Score 14/15 - Q1: Yes Q2: No Q3: Yes Q4: 5* Q5: Yes Q6: 4* Q7: 5* - Excellent fit...**",
  "timestamp": "{\"timestamp\": \"2025-01-17T14:00:00Z\"}"
}
```

### Testing the Webhook

Using cURL:
```bash
curl -X POST http://localhost:5000/webhook/submit \
  -H "Content-Type: application/json" \
  -d '{
    "client": "EDF Trading - Internship",
    "jobDescription": "Summer internship position",
    "applications": [
      {
        "User": "1",
        "Question 1": "I want this role because...",
        "Question 2": "My strengths include...",
        "Question 3": "A challenge I faced was..."
      }
    ]
  }'
```

Using Python:
```python
import requests

payload = {
    "client": "EDF Trading - Internship",
    "jobDescription": "Summer internship position",
    "applications": [
        {
            "User": "1",
            "Question 1": "I want this role because...",
            "Question 2": "My strengths include...",
            "Question 3": "A challenge I faced was..."
        }
    ]
}

response = requests.post(
    "http://localhost:5000/webhook/submit",
    json=payload
)

print(response.json())
```
