from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

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
        max_score = 35 if num_questions == 7 else 15
        
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

        For each candidate, provide the format: "User [number] - Overall Score [X]/{max_score} - Q1: [X]* Q2: [X]* Q3: [X]*{' Q4: [X]* Q5: [X]* Q6: [X]* Q7: [X]*' if num_questions == 7 else (' Q4: [X]* Q5: [X]* Q6: [X]*' if num_questions == 6 else '')} - [brief reason]"
        
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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

