from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

# Webhook configuration
OUTGOING_WEBHOOK_URL = os.getenv('OUTGOING_WEBHOOK_URL', '')

@app.route('/analyze', methods=['POST'])
def analyze_csv():
    try:
        data = request.json
        
        # Extract data from request
        client = data.get('client')
        job_description = data.get('jobDescription')
        supporting_references = data.get('supportingReferences', '')
        csv_data = data.get('csvData')
        user_count = data.get('userCount')
        
        if not all([client, job_description, csv_data, user_count]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create analysis prompt with ALL candidates
        # Load client criteria
        client_criteria = None
        try:
            with open('../ultils/clients.json', 'r') as f:
                clients_data = json.load(f)
                for c in clients_data['clients']:
                    if c['name'] == client:
                        client_criteria = c.get('Criteria', {})
                        break
        except Exception as e:
            print(f"Warning: Could not load client criteria: {e}")

        # Build criteria string for all questions
        criteria_text = ""
        if isinstance(client_criteria, dict):
            for question_num, criteria in client_criteria.items():
                criteria_text += f"\n{question_num}:\n{criteria}\n"
        else:
            criteria_text = client_criteria if client_criteria else 'No specific criteria provided'

        # Determine number of questions based on client
        num_questions = 7 if "Graduate" in client else 3
        max_score = 15 if num_questions == 7 else 15  # For 7-question format, only 3 questions are scored (Q4, Q6, Q7)
        
        # Add supporting references if provided
        supporting_text = f"\n\nSupporting References:\n{supporting_references}" if supporting_references else ""
        
        prompt = f"""Analyze the following job applications for {client}:

        Job Description: {job_description}{supporting_text}

        Number of Applications: {user_count}

        ALL Applications Data:
        {json.dumps(csv_data, indent=2)}

        Client Scoring Criteria ({num_questions} Questions):
        {criteria_text}

        Please analyze each application based on the client's specific scoring criteria above.
        For EACH of the {num_questions} questions, score each candidate from 1-5 stars based on how well their answer matches the criteria:
        - 1* = Meets 1-star criteria
        - 2* = Meets 2-star criteria  
        - 3* = Meets 3-star criteria
        - 4* = Meets 4-star criteria
        - 5* = Meets 5-star criteria

        IMPORTANT: Calculate the OVERALL SCORE as the SUM of all {num_questions} individual question scores (max {max_score} stars).

        For each candidate, provide the format EXACTLY as shown: 
        - For 3-question format: "1. **User [number] - Overall Score [X]/15 - Q1: [X]* Q2: [X]* Q3: [X]* - [brief reason]**"
        - For 6-question format: "1. **User [number] - Overall Score [X]/30 - Q1: [X]* Q2: [X]* Q3: [X]* Q4: [X]* Q5: [X]* Q6: [X]* - [brief reason]**"
        - For 7-question format: "1. **User [number] - Overall Score **[X]/15** - Q1: Yes/No Q2: Yes/No Q3: Yes/No Q4: [X]* Q5: Yes/No Q6: [X]* Q7: [X]* - [brief reason]**"
        
        IMPORTANT: For 7-question format:
        - DO NOT use brackets around Yes/No answers (write "Q1: Yes" not "Q1: [Yes]")
        - Only Q4, Q6, and Q7 are scored (1-5*), Q1, Q2, Q3, and Q5 are Yes/No informational questions
        - Use the numbered list format with bold markdown
        
        After the main analysis, provide detailed reasoning for each user in this format:
        "DETAILED REASONING:
        User [number]: [Detailed explanation of why they received this score, including specific examples from their answers and how they align with the scoring criteria]"
        
        Add a short summary of the analysis at the end for each user - keep within one line"""

        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert HR analyst. Provide clear, actionable insights about job applications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        # Create/refresh candidates.json with all candidates
        candidates_data = {
            'client': client,
            'jobDescription': job_description,
            'totalCandidates': user_count,
            'candidates': csv_data,
            'analysis': analysis,
            'timestamp': json.dumps({'timestamp': '2025-01-17T14:00:00Z'})
        }
        
        # Write to ultils/candidates.json (refresh on each run)
        candidates_file_path = '../ultils/candidates.json'
        try:
            with open(candidates_file_path, 'w') as f:
                json.dump(candidates_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write candidates.json: {e}")
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'userCount': user_count,
            'client': client
        })
        
    except Exception as e:
        print(f"Error in analyze_csv: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/submit', methods=['POST'])
def webhook_submit():
    """
    Incoming webhook endpoint that receives application submissions,
    analyzes them, and forwards to outgoing webhook
    
    Expected JSON format:
    {
        "client": "Client Name",
        "jobDescription": "Job description",
        "supportingReferences": "Optional references",
        "applications": [
            {
                "User": "1",
                "Question 1": "answer...",
                ...
            }
        ]
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        client = data.get('client')
        job_description = data.get('jobDescription')
        applications = data.get('applications', [])
        supporting_references = data.get('supportingReferences', '')
        
        if not all([client, job_description, applications]):
            return jsonify({'error': 'Missing required fields: client, jobDescription, applications'}), 400
        
        user_count = len(applications)
        
        # Load client criteria
        client_criteria = None
        try:
            with open('../ultils/clients.json', 'r') as f:
                clients_data = json.load(f)
                for c in clients_data['clients']:
                    if c['name'] == client:
                        client_criteria = c.get('Criteria', {})
                        break
        except Exception as e:
            print(f"Warning: Could not load client criteria: {e}")

        # Build criteria string for all questions
        criteria_text = ""
        if isinstance(client_criteria, dict):
            for question_num, criteria in client_criteria.items():
                criteria_text += f"\n{question_num}:\n{criteria}\n"
        else:
            criteria_text = client_criteria if client_criteria else 'No specific criteria provided'

        # Determine number of questions based on client
        num_questions = 7 if "Graduate" in client else 3
        max_score = 15 if num_questions == 7 else 15
        
        # Add supporting references if provided
        supporting_text = f"\n\nSupporting References:\n{supporting_references}" if supporting_references else ""
        
        prompt = f"""Analyze the following job applications for {client}:

        Job Description: {job_description}{supporting_text}

        Number of Applications: {user_count}

        ALL Applications Data:
        {json.dumps(applications, indent=2)}

        Client Scoring Criteria ({num_questions} Questions):
        {criteria_text}

        Please analyze each application based on the client's specific scoring criteria above.
        For EACH of the {num_questions} questions, score each candidate from 1-5 stars based on how well their answer matches the criteria:
        - 1* = Meets 1-star criteria
        - 2* = Meets 2-star criteria  
        - 3* = Meets 3-star criteria
        - 4* = Meets 4-star criteria
        - 5* = Meets 5-star criteria

        IMPORTANT: Calculate the OVERALL SCORE as the SUM of all {num_questions} individual question scores (max {max_score} stars).

        For each candidate, provide the format EXACTLY as shown: 
        - For 3-question format: "1. **User [number] - Overall Score [X]/15 - Q1: [X]* Q2: [X]* Q3: [X]* - [brief reason]**"
        - For 6-question format: "1. **User [number] - Overall Score [X]/30 - Q1: [X]* Q2: [X]* Q3: [X]* Q4: [X]* Q5: [X]* Q6: [X]* - [brief reason]**"
        - For 7-question format: "1. **User [number] - Overall Score **[X]/15** - Q1: Yes/No Q2: Yes/No Q3: Yes/No Q4: [X]* Q5: Yes/No Q6: [X]* Q7: [X]* - [brief reason]**"
        
        IMPORTANT: For 7-question format:
        - DO NOT use brackets around Yes/No answers (write "Q1: Yes" not "Q1: [Yes]")
        - Only Q4, Q6, and Q7 are scored (1-5*), Q1, Q2, Q3, and Q5 are Yes/No informational questions
        - Use the numbered list format with bold markdown
        
        After the main analysis, provide detailed reasoning for each user in this format:
        "DETAILED REASONING:
        User [number]: [Detailed explanation of why they received this score, including specific examples from their answers and how they align with the scoring criteria]"
        
        Add a short summary of the analysis at the end for each user - keep within one line"""

        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert HR analyst. Provide clear, actionable insights about job applications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        # Prepare response payload
        response_payload = {
            'client': client,
            'jobDescription': job_description,
            'userCount': user_count,
            'applications': applications,
            'analysis': analysis,
            'timestamp': json.dumps({'timestamp': '2025-01-17T14:00:00Z'})
        }
        
        # Send to outgoing webhook if configured
        webhook_status = None
        if OUTGOING_WEBHOOK_URL:
            try:
                webhook_response = requests.post(
                    OUTGOING_WEBHOOK_URL,
                    json=response_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                webhook_status = {
                    'sent': True,
                    'status_code': webhook_response.status_code,
                    'url': OUTGOING_WEBHOOK_URL
                }
                print(f"Sent to outgoing webhook: {OUTGOING_WEBHOOK_URL} - Status: {webhook_response.status_code}")
            except Exception as e:
                webhook_status = {
                    'sent': False,
                    'error': str(e),
                    'url': OUTGOING_WEBHOOK_URL
                }
                print(f"Error sending to outgoing webhook: {e}")
        
        # Return success response
        return jsonify({
            'success': True,
            'analysis': analysis,
            'userCount': user_count,
            'client': client,
            'webhookStatus': webhook_status
        }), 200
        
    except Exception as e:
        print(f"Error in webhook_submit: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/raw', methods=['POST'])
def webhook_raw():
    """
    RAW webhook receiver - No AI processing, just logs and saves data
    Perfect for testing webhook integrations
    """
    try:
        data = request.json
        
        print("\n" + "="*80)
        print("📥 RAW WEBHOOK RECEIVED")
        print("="*80)
        print(f"Client: {data.get('client')}")
        print(f"Job Description: {data.get('jobDescription', '')[:100]}...")
        print(f"Number of Applications: {len(data.get('applications', []))}")
        print("\nApplications:")
        for i, app in enumerate(data.get('applications', []), 1):
            print(f"  User {i}:")
            for key, value in app.items():
                print(f"    {key}: {value[:50]}..." if len(str(value)) > 50 else f"    {key}: {value}")
        print("="*80 + "\n")
        
        # Save to a file for inspection
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../ultils/webhook_raw_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved to {filename}")
        except Exception as e:
            print(f"⚠️  Could not save to file: {e}")
        
        # Return success response
        return jsonify({
            'status': 'received',
            'message': 'Raw webhook data received successfully',
            'applications_count': len(data.get('applications', [])),
            'client': data.get('client'),
            'timestamp': datetime.datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error in webhook_raw: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/receive', methods=['POST'])
def webhook_receive():
    """
    Test webhook receiver endpoint
    This endpoint receives the analyzed data and logs it
    You can customize this to do whatever you need with the data
    (e.g., save to database, send email, trigger other processes)
    """
    try:
        data = request.json
        
        print("\n" + "="*80)
        print("📥 WEBHOOK RECEIVED (with analysis)")
        print("="*80)
        print(f"Client: {data.get('client')}")
        print(f"User Count: {data.get('userCount')}")
        print(f"Job Description: {data.get('jobDescription', '')[:100]}...")
        print("\nAnalysis Preview:")
        analysis = data.get('analysis', '')
        # Print first 500 characters of analysis
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print("="*80 + "\n")
        
        # Save to a file for inspection
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../ultils/webhook_received_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved to {filename}")
        except Exception as e:
            print(f"⚠️  Could not save to file: {e}")
        
        # Return success response
        return jsonify({
            'status': 'received',
            'message': 'Webhook data processed successfully',
            'received_count': data.get('userCount', 0)
        }), 200
        
    except Exception as e:
        print(f"❌ Error in webhook_receive: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sheets/unanalyzed', methods=['GET'])
def get_unanalyzed():
    """Get all unanalyzed applications from Google Sheets"""
    try:
        from sheets_api import get_unanalyzed_applications
        sheet_id = request.args.get('sheetId')
        gid = request.args.get('gid')
        print(f"Fetching unanalyzed applications from sheetId={sheet_id}, gid={gid}")
        applications = get_unanalyzed_applications(sheet_id, gid)
        return jsonify({
            'success': True,
            'count': len(applications),
            'applications': applications
        }), 200
    except Exception as e:
        print(f"Error getting unanalyzed applications: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/sheets/analyze', methods=['POST'])
def analyze_sheets():
    """Analyze selected applications and write back to Google Sheets"""
    try:
        from sheets_api import analyze_and_write_to_sheet
        
        data = request.json
        selected_rows = data.get('selectedRows', [])
        client = data.get('client')
        job_description = data.get('jobDescription')
        supporting_references = data.get('supportingReferences', '')
        sheet_id = data.get('sheetId')
        gid = data.get('gid')
        
        if not all([selected_rows, client, job_description]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        print(f"Analyzing applications for sheetId={sheet_id}, gid={gid}")
        result = analyze_and_write_to_sheet(selected_rows, client, job_description, supporting_references, sheet_id, gid)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error analyzing applications: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/clients', methods=['GET'])
def get_clients():
    """Get list of all clients"""
    try:
        from sheets_api import get_clients_list
        sheet_id = request.args.get('sheetId')
        clients = get_clients_list(sheet_id)
        return jsonify({
            'success': True,
            'clients': clients
        }), 200
    except Exception as e:
        print(f"Error getting clients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/clients', methods=['POST'])
def add_client():
    """Add a new client with criteria"""
    try:
        from sheets_api import add_client_to_sheet
        
        data = request.json
        client_name = data.get('clientName')
        criteria = data.get('criteria', {})
        sheet_id = data.get('sheetId')
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        result = add_client_to_sheet(client_name, criteria, sheet_id)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error adding client: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/clients', methods=['DELETE'])
def delete_client():
    """Delete a client"""
    try:
        from sheets_api import delete_client_from_sheet
        
        data = request.json
        client_name = data.get('clientName')
        sheet_id = data.get('sheetId')
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        result = delete_client_from_sheet(client_name, sheet_id)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error deleting client: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

