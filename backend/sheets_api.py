#!/usr/bin/env python3
"""
Google Sheets API endpoints for frontend integration
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv
import openai
from datetime import datetime
import re

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
DEFAULT_SPREADSHEET_ID = "1jDJDQXPoZE6NTAqfTaCILv8ULXpM_vl5WeiEVSplChU"
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_spreadsheet(sheet_id=None):
    """Get authenticated spreadsheet connection"""
    creds = Credentials.from_service_account_file('google_credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet_id = sheet_id or DEFAULT_SPREADSHEET_ID
    return client.open_by_key(spreadsheet_id)

def get_unanalyzed_applications(sheet_id=None):
    """
    Get all applications that don't have analysis yet (column V is empty)
    Returns list of applications with row numbers
    """
    spreadsheet = get_spreadsheet(sheet_id)
    worksheet = spreadsheet.get_worksheet(0)
    
    all_values = worksheet.get_all_values()
    headers = all_values[0]
    
    # Column V is column 22 (index 21)
    ANALYSIS_START_COL = 21  # Column V (0-indexed)
    
    unanalyzed = []
    
    for row_idx, row in enumerate(all_values[1:], start=2):  # Start from row 2 (skip header)
        # Check if column V (analysis column) is empty
        has_analysis = len(row) > ANALYSIS_START_COL and row[ANALYSIS_START_COL].strip()
        
        if not has_analysis and row:  # Has data but no analysis
            application = {
                'row_number': row_idx,
                'first_name': row[2] if len(row) > 2 else '',  # Col C
                'surname': row[3] if len(row) > 3 else '',  # Col D
                'email': row[4] if len(row) > 4 else '',  # Col E
                'university': row[7] if len(row) > 7 else '',  # Col H
                'course': row[8] if len(row) > 8 else '',  # Col I
                'right_to_work': row[10] if len(row) > 10 else '',  # Col K
                'visa_sponsorship': row[11] if len(row) > 11 else '',  # Col L
                'gcse_maths': row[12] if len(row) > 12 else '',  # Col M
                'available_sept_2026': row[13] if len(row) > 13 else '',  # Col N
                'understanding_of_role': row[14] if len(row) > 14 else '',  # Col O
                'why_edf': row[15] if len(row) > 15 else '',  # Col P
                'what_stands_out': row[16] if len(row) > 16 else '',  # Col Q
                'registration_date': row[19] if len(row) > 19 else '',  # Col T
            }
            unanalyzed.append(application)
    
    return unanalyzed

def analyze_and_write_to_sheet(selected_rows, client, job_description, supporting_references='', sheet_id=None):
    """
    Analyze selected applications and write results back to the spreadsheet
    """
    spreadsheet = get_spreadsheet(sheet_id)
    worksheet = spreadsheet.get_worksheet(0)
    
    all_values = worksheet.get_all_values()
    
    # Build applications data for selected rows
    applications = []
    for row_num in selected_rows:
        row = all_values[row_num - 1]  # Convert to 0-indexed
        app = {
            'row_number': row_num,
            'first_name': row[2] if len(row) > 2 else '',
            'surname': row[3] if len(row) > 3 else '',
            'university': row[7] if len(row) > 7 else '',
            'course': row[8] if len(row) > 8 else '',
            'right_to_work': row[10] if len(row) > 10 else '',
            'visa_sponsorship': row[11] if len(row) > 11 else '',
            'gcse_maths': row[12] if len(row) > 12 else '',
            'available_sept_2026': row[13] if len(row) > 13 else '',
            'understanding_of_role': row[14] if len(row) > 14 else '',
            'why_edf': row[15] if len(row) > 15 else '',
            'what_stands_out': row[16] if len(row) > 16 else '',
        }
        applications.append(app)
    
    # Analyze with AI
    analysis = analyze_applications_ai(applications, client, job_description, supporting_references)
    
    if not analysis:
        return {'error': 'Analysis failed'}
    
    # Parse analysis and write to each row
    results = []
    failed_rows = []
    
    for app in applications:
        row_num = app['row_number']
        scores = extract_scores_for_row(analysis, row_num, all_values)
        
        if scores:
            try:
                # Extract numeric scores from strings like "4*" or "13/15"
                overall_num = scores.get('overall_score', '').split('/')[0] if '/' in scores.get('overall_score', '') else ''
                q4_num = scores.get('q4_score', '').replace('*', '') if scores.get('q4_score') else ''
                q6_num = scores.get('q6_score', '').replace('*', '') if scores.get('q6_score') else ''
                q7_num = scores.get('q7_score', '').replace('*', '') if scores.get('q7_score') else ''
                
                # Create formulas for star rendering
                q4_formula = f'=REPT(CHAR(9733),{q4_num})' if q4_num.isdigit() else scores.get('q4_score', '')
                q6_formula = f'=REPT(CHAR(9733),{q6_num})' if q6_num.isdigit() else scores.get('q6_score', '')
                q7_formula = f'=REPT(CHAR(9733),{q7_num})' if q7_num.isdigit() else scores.get('q7_score', '')
                
                # Write to columns V onwards (column 22, index 21)
                # V: Overall Score, W: Q4, X: Q6, Y: Q7, Z: Brief Reason, AA: Detailed Reasoning, AB: Analyzed Date, AC: Client, AD: Job Description
                cell_range = f'V{row_num}:AD{row_num}'
                values = [[
                    scores.get('overall_score', ''),
                    q4_formula,
                    q6_formula,
                    q7_formula,
                    scores.get('brief_reason', ''),
                    scores.get('detailed_reasoning', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    client,
                    job_description
                ]]
                
                # Use value_input_option='USER_ENTERED' to interpret formulas instead of text
                worksheet.update(values=values, range_name=cell_range, value_input_option='USER_ENTERED')
                results.append({
                    'row': row_num,
                    'name': f"{app['first_name']} {app['surname']}",
                    'score': scores.get('overall_score', 'N/A')
                })
            except Exception as e:
                print(f"Error writing row {row_num}: {e}")
                failed_rows.append({
                    'row': row_num,
                    'name': f"{app['first_name']} {app['surname']}",
                    'error': str(e)
                })
        else:
            # AI didn't generate a score for this row
            failed_rows.append({
                'row': row_num,
                'name': f"{app['first_name']} {app['surname']}",
                'error': 'No scores found in AI analysis'
            })
    
    return {
        'success': True,
        'analyzed_count': len(results),
        'failed_count': len(failed_rows),
        'results': results,
        'failed': failed_rows
    }

def analyze_applications_ai(applications, client, job_description, supporting_references=''):
    """Analyze applications using OpenAI"""
    
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
    
    criteria_text = ""
    if isinstance(client_criteria, dict):
        for question_num, criteria in client_criteria.items():
            criteria_text += f"\n{question_num}:\n{criteria}\n"
    else:
        criteria_text = client_criteria if client_criteria else 'No specific criteria provided'
    
    supporting_text = f"\n\nSupporting References:\n{supporting_references}" if supporting_references else ""
    
    # Format applications with row numbers
    apps_formatted = []
    for app in applications:
        apps_formatted.append({
            'Row': app['row_number'],
            'Name': f"{app['first_name']} {app['surname']}",
            'University': app['university'],
            'Course': app['course'],
            'Understanding_of_role': app['understanding_of_role'],
            'Why_EDF': app['why_edf'],
            'What_stands_out': app['what_stands_out']
        })
    
    prompt = f"""Analyze the following job applications for {client}:

Job Description: {job_description}{supporting_text}

Number of Applications: {len(applications)}

Applications Data:
{json.dumps(apps_formatted, indent=2)}

Client Scoring Criteria (7 Questions):
{criteria_text}

For the 7-question Graduate Scheme format:
- Q4: "Understanding of role" (1-5 stars)
- Q6: "Why EDF Trading" (1-5 stars)  
- Q7: "What stands out about this position" (1-5 stars)

IMPORTANT: Calculate the OVERALL SCORE as the SUM of Q4, Q6, and Q7 (max 15 stars).

For each candidate, provide the format EXACTLY as shown:
"Row [row_number] - Overall Score **[X]/15** - Q4: [X]* Q6: [X]* Q7: [X]* - [brief reason]"

After the main analysis, provide detailed reasoning:
"DETAILED REASONING:
Row [row_number]: [Detailed explanation]"
"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert HR analyst for EDF Trading."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return None

def extract_scores_for_row(analysis, row_number, all_values):
    """Extract scores from analysis for a specific row"""
    lines = analysis.split('\n')
    
    for i, line in enumerate(lines):
        if f"Row {row_number}" in line and "Overall Score" in line:
            # Extract scores
            score_match = re.search(r'Overall Score\s+\*?\*?(\d+)/15', line)
            q4_match = re.search(r'Q4:\s*(\d+)\*', line)
            q6_match = re.search(r'Q6:\s*(\d+)\*', line)
            q7_match = re.search(r'Q7:\s*(\d+)\*', line)
            reason_match = re.search(r'-\s*([^*\n]+?)(?:\*\*)?$', line)
            
            # Find detailed reasoning
            detailed_reasoning = ''
            for j, detail_line in enumerate(lines):
                if f"Row {row_number}:" in detail_line and "DETAILED REASONING" in '\n'.join(lines[:j]):
                    detailed_reasoning = detail_line.replace(f"Row {row_number}:", "").strip()
                    break
            
            return {
                'overall_score': f"{score_match.group(1)}/15" if score_match else 'N/A',
                'q4_score': f"{q4_match.group(1)}*" if q4_match else 'N/A',
                'q6_score': f"{q6_match.group(1)}*" if q6_match else 'N/A',
                'q7_score': f"{q7_match.group(1)}*" if q7_match else 'N/A',
                'brief_reason': reason_match.group(1).strip() if reason_match else 'N/A',
                'detailed_reasoning': detailed_reasoning or 'N/A'
            }
    
    return None

if __name__ == "__main__":
    # Test getting unanalyzed applications
    print("Testing get_unanalyzed_applications()...")
    apps = get_unanalyzed_applications()
    print(f"\nFound {len(apps)} unanalyzed applications:")
    for app in apps[:5]:  # Show first 5
        print(f"  Row {app['row_number']}: {app['first_name']} {app['surname']} - {app['university']}")

