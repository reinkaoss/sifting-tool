from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract parameters
            selected_rows = data.get('selectedRows', [])
            client = data.get('client')
            job_description = data.get('jobDescription')
            supporting_references = data.get('supportingReferences', '')
            sheet_id = data.get('sheetId')
            gid = data.get('gid')
            
            # Import here to avoid cold start issues
            from sheets_api import analyze_and_write_to_sheet
            
            result = analyze_and_write_to_sheet(
                selected_rows,
                client,
                job_description,
                supporting_references,
                sheet_id,
                gid
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {'error': str(e), 'success': False}
            self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

