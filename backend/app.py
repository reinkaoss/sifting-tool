from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def average_analysis_scores(analyses, user_count):
    """
    Average scores from multiple analysis runs.
    Keep text from first run, but average all scores.
    
    Args:
        analyses: List of 3 analysis strings
        user_count: Number of users analyzed
    
    Returns:
        String with averaged scores and text from first run
    """
    # Parse all analyses to extract scores
    all_user_scores = {}  # {user_num: {run_num: {overall, q1, q2, ...}}}
    
    for run_idx, analysis in enumerate(analyses, 1):
        lines = analysis.split('\n')
        for line in lines:
            # Look for user patterns like "User 1 -" or "1. **User 1"
            user_match = re.search(r'(?:User\s+|^\d+\.\s*\*\*User\s+)(\d+)', line)
            if user_match and 'Overall Score' in line:
                user_num = user_match.group(1)
                
                if user_num not in all_user_scores:
                    all_user_scores[user_num] = {}
                
                # Extract overall score
                overall_match = re.search(r'Overall Score[*\s]+(\d+\.?\d*)/(\d+)', line)
                
                # Extract individual question scores (Q1, Q2, Q3, etc.)
                q_scores = {}
                for q_num in range(1, 10):  # Support up to Q9
                    # Try numeric scores first
                    q_match = re.search(rf'Q{q_num}:\s*(\d+\.?\d*)\*', line)
                    if q_match:
                        q_scores[f'q{q_num}'] = float(q_match.group(1))
                    else:
                        # Try Yes/No answers
                        yesno_match = re.search(rf'Q{q_num}:\s*(Yes|No)', line, re.IGNORECASE)
                        if yesno_match:
                            q_scores[f'q{q_num}'] = yesno_match.group(1)
                
                all_user_scores[user_num][run_idx] = {
                    'overall': float(overall_match.group(1)) if overall_match else 0,
                    'max_score': int(overall_match.group(2)) if overall_match else 15,
                    'questions': q_scores
                }
    
    # Calculate averages for each user
    averaged_scores = {}
    for user_num, runs in all_user_scores.items():
        if not runs:
            continue
            
        # Average overall scores
        overall_scores = [run['overall'] for run in runs.values()]
        avg_overall = sum(overall_scores) / len(overall_scores)
        max_score = runs[1]['max_score'] if 1 in runs else 15
        
        # Average question scores (only numeric ones)
        avg_questions = {}
        all_q_keys = set()
        for run in runs.values():
            all_q_keys.update(run['questions'].keys())
        
        for q_key in all_q_keys:
            q_values = []
            for run in runs.values():
                val = run['questions'].get(q_key)
                if val and isinstance(val, (int, float)):
                    q_values.append(val)
            
            if q_values:
                avg_questions[q_key] = sum(q_values) / len(q_values)
            else:
                # Keep Yes/No as-is from first run
                avg_questions[q_key] = runs[1]['questions'].get(q_key, 'N/A')
        
        averaged_scores[user_num] = {
            'overall': avg_overall,
            'max_score': max_score,
            'questions': avg_questions
        }
    
    # Now rebuild the analysis using first run's text but with averaged scores
    result_lines = []
    first_analysis_lines = analyses[0].split('\n')
    
    for line in first_analysis_lines:
        # Check if this line contains a user score
        user_match = re.search(r'(?:User\s+|^\d+\.\s*\*\*User\s+)(\d+)', line)
        if user_match and 'Overall Score' in line and user_match.group(1) in averaged_scores:
            user_num = user_match.group(1)
            scores = averaged_scores[user_num]
            
            # Rebuild the line with averaged scores
            # Extract the part after the scores (the brief reason)
            reason_match = re.search(r'-\s*([^*\n]+?)(?:\*\*)?$', line)
            brief_reason = reason_match.group(1).strip() if reason_match else ''
            
            # Build new score line
            score_parts = []
            for q_key in sorted(scores['questions'].keys(), key=lambda x: int(re.search(r'\d+', x).group())):
                q_num = re.search(r'\d+', q_key).group()
                val = scores['questions'][q_key]
                if isinstance(val, (int, float)):
                    score_parts.append(f"Q{q_num}: {val:.2f}*")
                else:
                    score_parts.append(f"Q{q_num}: {val}")
            
            # Reconstruct the line
            if line.strip().startswith(str(user_num) + '.'):
                new_line = f"{user_num}. **User {user_num} - Overall Score {scores['overall']:.2f}/{scores['max_score']} - {' '.join(score_parts)} - {brief_reason}**"
            else:
                new_line = f"**User {user_num} - Overall Score {scores['overall']:.2f}/{scores['max_score']} - {' '.join(score_parts)} - {brief_reason}**"
            
            result_lines.append(new_line)
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines)

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
        For EACH of the {num_questions} questions, score each candidate from 1.00-5.00 stars (using 2 decimal places) based on how well their answer matches the criteria:
        - 1.00-1.99* = Poor match to criteria
        - 2.00-2.99* = Below average match to criteria  
        - 3.00-3.99* = Average match to criteria
        - 4.00-4.99* = Good match to criteria
        - 5.00* = Excellent match to criteria
        
        USE DECIMAL SCORES (e.g., 3.25*, 4.75*, 2.50*) to provide nuanced differentiation between candidates.

        IMPORTANT: Calculate the OVERALL SCORE as the SUM of all {num_questions} individual question scores (max {max_score} stars). Express the overall score to 2 decimal places.

        For each candidate, provide the format EXACTLY as shown (use decimal scores with 2 decimal places): 
        - For 3-question format: "1. **User [number] - Overall Score [X.XX]/15 - Q1: [X.XX]* Q2: [X.XX]* Q3: [X.XX]* - [brief reason]**"
        - For 6-question format: "1. **User [number] - Overall Score [X.XX]/30 - Q1: [X.XX]* Q2: [X.XX]* Q3: [X.XX]* Q4: [X.XX]* Q5: [X.XX]* Q6: [X.XX]* - [brief reason]**"
        - For 7-question format: "1. **User [number] - Overall Score **[X.XX]/15** - Q1: Yes/No Q2: Yes/No Q3: Yes/No Q4: [X.XX]* Q5: Yes/No Q6: [X.XX]* Q7: [X.XX]* - [brief reason]**"
        
        IMPORTANT: For 7-question format:
        - DO NOT use brackets around Yes/No answers (write "Q1: Yes" not "Q1: [Yes]")
        - Only Q4, Q6, and Q7 are scored (1.00-5.00* with 2 decimals), Q1, Q2, Q3, and Q5 are Yes/No informational questions
        - Use the numbered list format with bold markdown
        
        CRITICAL: The [brief reason] MUST be maximum 1-2 sentences (20-30 words total) - professional but simple, NO question number mentions (don't say Q1, Q4, Q6, etc).
        Examples:
        - "Has a solid grasp of the role, dives into quantitative aspects. Excited about the hands-on learning and ties in personal growth."
        - "Shows a general idea of the role but lacks depth. Drawn to the market position but could've tied in more specifics."
        
        Add a short summary of the analysis at the end for each user - keep within one line"""

        # Call OpenAI API 3 times and average the scores for consistency
        print(f"\n🔄 Running 3 analysis passes for {user_count} candidates to ensure scoring consistency...")
        analyses = []
        for run_num in range(1, 4):
            print(f"  📊 Analysis run {run_num}/3...")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an early careers recruiter. CRITICAL: Use decimal scores with EXACTLY 2 decimal places (e.g., 3.75*, 4.25*, 12.50/15). Write brief reasons that are professional but simple - natural flow, NO question number mentions (don't say Q1, Q4, Q6, etc). Every candidate analysis must be completely unique - no templates, no copy-paste phrases. Keep brief reasons SHORT - 1-2 sentences max (20-30 words)."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0,
                top_p=1
            )
            analyses.append(response.choices[0].message.content)
        
        print("  ✅ Averaging scores from 3 runs...")
        # Average the scores from all 3 runs, keep text from first run
        analysis = average_analysis_scores(analyses, user_count)
        
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

@app.route('/sheets/analyzed', methods=['GET'])
def get_analyzed():
    """Get all analyzed applications from Google Sheets"""
    try:
        from sheets_api import get_analyzed_applications
        sheet_id = request.args.get('sheetId')
        gid = request.args.get('gid')
        print(f"Fetching analyzed applications from sheetId={sheet_id}, gid={gid}")
        applications = get_analyzed_applications(sheet_id, gid)
        return jsonify({
            'success': True,
            'count': len(applications),
            'applications': applications
        }), 200
    except Exception as e:
        print(f"Error getting analyzed applications: {str(e)}")
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

@app.route('/sheets/ai-detection', methods=['POST'])
def detect_ai_sheets():
    """Run AI detection on selected analyzed applications and write AI % to Google Sheets"""
    try:
        from sheets_api import detect_ai_and_write_to_sheet
        
        data = request.json
        selected_rows = data.get('selectedRows', [])
        sheet_id = data.get('sheetId')
        gid = data.get('gid')
        
        if not selected_rows:
            return jsonify({'error': 'No rows selected'}), 400
        
        print(f"Running AI detection for sheetId={sheet_id}, gid={gid}, rows={selected_rows}")
        result = detect_ai_and_write_to_sheet(selected_rows, sheet_id, gid)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error running AI detection: {str(e)}")
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

