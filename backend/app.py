from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/analyze', methods=['POST'])
def analyze_csv():
    print("🚀 NEW ANALYSIS REQUEST RECEIVED")
    try:
        data = request.json
        print(f"📊 Request data received: {len(data)} fields")
        
        # Extract data from request
        client = data.get('client')
        job_description = data.get('jobDescription')
        supporting_references = data.get('supportingReferences', '')
        csv_data = data.get('csvData')
        user_count = data.get('userCount')
        batch_number = data.get('batchNumber', 1)  # New parameter for batch number
        
        print(f"📋 Client: {client}")
        print(f"📄 Job description length: {len(job_description) if job_description else 0}")
        print(f"📝 Supporting references length: {len(supporting_references) if supporting_references else 0}")
        print(f"👥 User count: {user_count}")
        print(f"📊 CSV data length: {len(csv_data) if csv_data else 0}")
        print(f"🔄 Processing batch: {batch_number}")
        
        if not all([client, job_description, csv_data, user_count]):
            print("❌ Missing required fields")
            return jsonify({'error': 'Missing required fields'}), 400
        
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
        
        # Process single batch
        batch_size = 50
        start_idx = (batch_number - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(csv_data))
        batch_data = csv_data[start_idx:end_idx]
        
        print(f"🔄 Processing batch {batch_number} (applications {start_idx+1} to {end_idx} of {len(csv_data)})")
        print(f"   📊 Applications in this batch: {len(batch_data)}")
        
        prompt = f"""Analyze the following job applications for {client} (Batch {batch_number}):

Job Description: {job_description}{supporting_text}

Number of Applications in this batch: {len(batch_data)}
Total Applications: {user_count}
Batch Progress: {batch_number}/{(len(csv_data) + batch_size - 1) // batch_size}

Applications Data for this batch:
{json.dumps(batch_data, indent=2)}

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

        # Call OpenAI API for this batch
        print(f"   🤖 Sending request to OpenAI API...")
        batch_start_time = time.time()
        
        try:
            print(f"   ⏳ Waiting for OpenAI response (this may take up to 60 seconds)...")
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst. Provide clear, actionable insights about job applications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7,
                timeout=60  # 60 second timeout
            )
            
            api_time = time.time() - batch_start_time
            print(f"   ✅ API response received in {api_time:.1f} seconds")
            
            batch_analysis = response.choices[0].message.content
            
            print(f"   📝 Batch {batch_number} analysis completed ({len(batch_analysis)} characters)")
            print(f"   ⏱️  Batch processing time: {api_time:.1f} seconds")
            print("   " + "="*50)
            
            # Return immediate results for this batch
            return jsonify({
                'success': True,
                'analysis': batch_analysis,
                'batchNumber': batch_number,
                'totalBatches': (len(csv_data) + batch_size - 1) // batch_size,
                'isComplete': end_idx >= len(csv_data),
                'processedCount': end_idx,
                'totalCount': len(csv_data)
            })
            
        except Exception as e:
            print(f"   ❌ Error processing batch {batch_number}: {str(e)}")
            print(f"   🔄 Retrying batch {batch_number}...")
            
            try:
                # Retry once with a simpler prompt
                simple_prompt = f"""Analyze these {len(batch_data)} job applications for {client}:

Applications: {json.dumps(batch_data, indent=2)}

Score each candidate 1-5 stars for each question and provide format: "User [number] - Overall Score [X]/{max_score} - Q1: [X]* Q2: [X]* Q3: [X]* - [brief reason]"
"""
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert HR analyst."},
                        {"role": "user", "content": simple_prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7,
                    timeout=30
                )
                
                batch_analysis = response.choices[0].message.content
                print(f"   ✅ Batch {batch_number} retry successful")
                
                return jsonify({
                    'success': True,
                    'analysis': batch_analysis,
                    'batchNumber': batch_number,
                    'totalBatches': (len(csv_data) + batch_size - 1) // batch_size,
                    'isComplete': end_idx >= len(csv_data),
                    'processedCount': end_idx,
                    'totalCount': len(csv_data)
                })
                
            except Exception as retry_error:
                print(f"   ❌ Batch {batch_number} failed after retry: {str(retry_error)}")
                # Return error for this batch
                return jsonify({
                    'success': False,
                    'error': f'Batch {batch_number} failed: {str(retry_error)}',
                    'batchNumber': batch_number,
                    'totalBatches': (len(csv_data) + batch_size - 1) // batch_size,
                    'isComplete': False,
                    'processedCount': end_idx,
                    'totalCount': len(csv_data)
                }), 500
            
    except Exception as e:
        print(f"Error in analyze_csv: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    app.run(debug=False, port=5002, use_reloader=False)

