from http.server import BaseHTTPRequestHandler
import json
import os
import base64

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            
            response = {
                'has_env_var': bool(creds_json),
                'length': len(creds_json) if creds_json else 0,
                'first_10_chars': creds_json[:10] if creds_json else None,
                'is_base64': False,
                'decoded_preview': None,
                'error': None
            }
            
            if creds_json:
                try:
                    # Try to decode as base64
                    decoded = base64.b64decode(creds_json).decode('utf-8')
                    response['is_base64'] = True
                    response['decoded_preview'] = decoded[:100]  # First 100 chars
                    
                    # Try to parse as JSON
                    parsed = json.loads(decoded)
                    response['has_type'] = 'type' in parsed
                    response['has_private_key'] = 'private_key' in parsed
                except Exception as e:
                    response['error'] = str(e)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response).encode())

