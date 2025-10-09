from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        creds_raw = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON', '')
        
        response = {
            'has_google_creds': bool(creds_raw),
            'creds_length': len(creds_raw),
            'first_20_chars': creds_raw[:20] if creds_raw else None,
            'last_20_chars': creds_raw[-20:] if creds_raw and len(creds_raw) > 20 else None,
            'has_openai_key': bool(os.getenv('OPENAI_API_KEY')),
            'all_env_vars': list(os.environ.keys())[:20]  # First 20 env var names
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())

