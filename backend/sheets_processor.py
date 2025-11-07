#!/usr/bin/env python3
"""
Google Sheets Integration for EDF Trading Application Analysis
Reads applications from Google Sheets and writes AI analysis to a new tab
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv
import openai
from datetime import datetime

# Load environment variables
load_dotenv()

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1jDJDQXPoZE6NTAqfTaCILv8ULXpM_vl5WeiEVSplChU/edit?gid=0#gid=0"
SPREADSHEET_ID = "1jDJDQXPoZE6NTAqfTaCILv8ULXpM_vl5WeiEVSplChU"

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')

# Column mapping based on your headers
COLUMN_MAPPING = {
    'Form_ID': 0,
    'University': 1,
    'Course': 2,
    'CV': 3,
    'Right_to_work': 4,
    'Visa_sponsorship': 5,
    'GCSE_Maths': 6,
    'Available_Sept_2026': 7,
    'Understanding_of_role': 8,
    'Why_EDF': 9,
    'What_stands_out': 10,
    'Create_account': 11,
    'Privacy_statement': 12,
    'Registration_Date': 13
}

def connect_to_sheet():
    """Connect to Google Sheets using service account credentials"""
    try:
        # Load credentials from service account file
        creds = Credentials.from_service_account_file(
            'google_credentials.json',
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        return spreadsheet
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        print("\nMake sure you have:")
        print("1. Created a service account in Google Cloud Console")
        print("2. Downloaded the credentials JSON file")
        print("3. Saved it as 'google_credentials.json' in the backend folder")
        print("4. Shared your spreadsheet with the service account email")
        return None

def read_applications(spreadsheet):
    """Read all applications from the first sheet"""
    try:
        # Get the first worksheet (where form data is)
        worksheet = spreadsheet.get_worksheet(0)
        
        # Get all values
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            print("No data found in spreadsheet")
            return []
        
        headers = all_values[0]
        data_rows = all_values[1:]
        
        # Convert to list of dictionaries
        applications = []
        for row in data_rows:
            if not row or not row[0]:  # Skip empty rows
                continue
            
            app = {}
            for i, header in enumerate(headers):
                app[header] = row[i] if i < len(row) else ''
            applications.append(app)
        
        print(f"✅ Read {len(applications)} applications from sheet")
        return applications
    
    except Exception as e:
        print(f"Error reading applications: {e}")
        return []

def analyze_applications(applications, client="EDF Trading - Graduate Scheme"):
    """Analyze applications using OpenAI"""
    
    if not applications:
        return []
    
    # The 3 key questions for analysis (matching your 7-question format)
    # Q1-Q3 are Yes/No, Q4-Q7 include the scored questions
    
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
    
    # Build criteria string
    criteria_text = ""
    if isinstance(client_criteria, dict):
        for question_num, criteria in client_criteria.items():
            criteria_text += f"\n{question_num}:\n{criteria}\n"
    else:
        criteria_text = client_criteria if client_criteria else 'No specific criteria provided'
    
    prompt = f"""Analyze the following job applications for {client}:

Number of Applications: {len(applications)}

Applications Data:
{json.dumps(applications, indent=2)}

Client Scoring Criteria (7 Questions):
{criteria_text}

For the 7-question Graduate Scheme format:
- Q1-Q3 and Q5 are Yes/No informational questions (use data from: Right to work, Visa sponsorship, GCSE Maths, Available Sept 2026)
- Q4: "Understanding of role" (1.00-5.00 stars with 2 decimal places based on their answer)
- Q6: "Why EDF Trading" (1.00-5.00 stars with 2 decimal places based on their answer)  
- Q7: "What stands out about this position" (1.00-5.00 stars with 2 decimal places based on their answer)

IMPORTANT: Calculate the OVERALL SCORE as the SUM of Q4, Q6, and Q7 (max 15 stars). Express as a decimal with 2 decimal places.
USE DECIMAL SCORES (e.g., 3.25*, 4.75*, 2.50*) to provide nuanced differentiation between candidates.

For each candidate, provide the format EXACTLY as shown (use decimal scores with 2 decimal places):
"1. **User [Form_ID] - Overall Score **[X.XX]/15** - Q1: Yes/No Q2: Yes/No Q3: Yes/No Q4: [X.XX]* Q5: Yes/No Q6: [X.XX]* Q7: [X.XX]* - [brief reason]**"

DO NOT use brackets around Yes/No answers (write "Q1: Yes" not "Q1: [Yes]")

After the main analysis, provide detailed reasoning for each user in this format:
"DETAILED REASONING:
User [Form_ID]: [Detailed explanation of why they received this score, including specific examples from their answers and how they align with the scoring criteria]"
"""
    
    try:
        print("🤖 Analyzing applications with AI...")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert HR analyst for EDF Trading. CRITICAL: Use decimal scores with EXACTLY 2 decimal places (e.g., 3.75*, 4.25*, 12.50/15). Provide clear, actionable insights about job applications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0,  # Deterministic scoring - no variation
            top_p=1  # Disable nucleus sampling for maximum consistency
        )
        
        analysis = response.choices[0].message.content
        print("✅ AI analysis completed")
        return analysis
        
    except Exception as e:
        print(f"❌ Error during AI analysis: {e}")
        return None

def parse_analysis_to_results(analysis, applications):
    """Parse AI analysis and create results for each application"""
    
    results = []
    lines = analysis.split('\n')
    
    for app in applications:
        form_id = app.get('Form_ID', '')
        
        # Find the analysis line for this form_id
        user_line = None
        detailed_reasoning = None
        
        for i, line in enumerate(lines):
            if f"User {form_id}" in line and "Overall Score" in line:
                user_line = line
                
            if f"User {form_id}:" in line and "DETAILED REASONING" in '\n'.join(lines[:i]):
                detailed_reasoning = line.replace(f"User {form_id}:", "").strip()
        
        if user_line:
            # Extract scores from the line (with decimal support)
            import re
            score_match = re.search(r'Overall Score\s+\*?\*?(\d+\.?\d*)/15', user_line)
            q4_match = re.search(r'Q4:\s*(\d+\.?\d*)\*', user_line)
            q6_match = re.search(r'Q6:\s*(\d+\.?\d*)\*', user_line)
            q7_match = re.search(r'Q7:\s*(\d+\.?\d*)\*', user_line)
            reason_match = re.search(r'-\s*([^*]+?)(?:\*\*)?$', user_line)
            
            overall_score = score_match.group(1) if score_match else 'N/A'
            q4_score = q4_match.group(1) if q4_match else 'N/A'
            q6_score = q6_match.group(1) if q6_match else 'N/A'
            q7_score = q7_match.group(1) if q7_match else 'N/A'
            brief_reason = reason_match.group(1).strip() if reason_match else 'N/A'
            
            results.append({
                'Form_ID': form_id,
                'University': app.get('University', ''),
                'Course': app.get('Course', ''),
                'Overall_Score': f"{overall_score}/15",
                'Q4_Understanding': f"{q4_score}*",
                'Q6_Why_EDF': f"{q6_score}*",
                'Q7_What_Stands_Out': f"{q7_score}*",
                'Brief_Reason': brief_reason,
                'Detailed_Reasoning': detailed_reasoning or 'N/A',
                'Analyzed_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return results

def write_results_to_sheet(spreadsheet, results):
    """Write analysis results to a new tab called 'AI Analysis'"""
    
    try:
        # Try to get existing 'AI Analysis' worksheet
        try:
            worksheet = spreadsheet.worksheet('AI Analysis')
            print("Found existing 'AI Analysis' tab, updating...")
        except:
            # Create new worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(title='AI Analysis', rows=1000, cols=20)
            print("Created new 'AI Analysis' tab")
        
        # Prepare headers
        headers = [
            'Form_ID',
            'University',
            'Course',
            'Overall_Score',
            'Q4_Understanding',
            'Q6_Why_EDF',
            'Q7_What_Stands_Out',
            'Brief_Reason',
            'Detailed_Reasoning',
            'Analyzed_Date'
        ]
        
        # Prepare data rows
        data_rows = []
        for result in results:
            row = [result.get(header, '') for header in headers]
            data_rows.append(row)
        
        # Clear existing data and write new data
        worksheet.clear()
        worksheet.update(values=[headers] + data_rows, range_name='A1')
        
        print(f"✅ Wrote {len(results)} analyzed results to 'AI Analysis' tab")
        
        # Format the header row (bold)
        worksheet.format('A1:J1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing results: {e}")
        return False

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("📊 EDF TRADING - GOOGLE SHEETS APPLICATION ANALYZER")
    print("=" * 80)
    
    # Connect to spreadsheet
    print("\n1. Connecting to Google Sheets...")
    spreadsheet = connect_to_sheet()
    if not spreadsheet:
        return
    
    # Read applications
    print("\n2. Reading applications...")
    applications = read_applications(spreadsheet)
    if not applications:
        print("No applications to process")
        return
    
    # Analyze applications
    print(f"\n3. Analyzing {len(applications)} applications...")
    analysis = analyze_applications(applications)
    if not analysis:
        return
    
    # Parse analysis to structured results
    print("\n4. Parsing analysis results...")
    results = parse_analysis_to_results(analysis, applications)
    
    # Write results back to sheet
    print("\n5. Writing results to 'AI Analysis' tab...")
    success = write_results_to_sheet(spreadsheet, results)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"\nProcessed: {len(results)} applications")
        print(f"View results: {SPREADSHEET_URL}")
        print("Check the 'AI Analysis' tab for detailed scores and reasoning")
        print("=" * 80)
    else:
        print("\n❌ Failed to write results")

if __name__ == "__main__":
    main()

