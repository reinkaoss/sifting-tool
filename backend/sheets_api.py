#!/usr/bin/env python3
"""
Google Sheets API endpoints for frontend integration
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
import base64
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import re

load_dotenv()

def average_analysis_scores_sheets(analyses):
    """
    Average scores from multiple analysis runs for sheets.
    Keep text from first run, but average all scores.
    Similar to app.py version but adapted for sheets format (Row-based).
    
    Returns:
        tuple: (averaged_analysis_text, raw_scores_by_row)
        raw_scores_by_row: {row_num: {'overall': [s1, s2, s3], 'q1': [s1, s2, s3], ...}}
    """
    all_row_scores = {}  # {row_num: {run_num: {overall, q1, q2, ...}}}
    
    for run_idx, analysis in enumerate(analyses, 1):
        lines = analysis.split('\n')
        for line in lines:
            # Look for Row patterns like "Row 2 -"
            row_match = re.search(r'Row\s+(\d+)', line)
            if row_match and 'Overall Score' in line:
                row_num = row_match.group(1)
                
                if row_num not in all_row_scores:
                    all_row_scores[row_num] = {}
                
                # Extract overall score - try multiple patterns (with and without /max_score)
                overall_score = 0
                max_score_val = 15  # default
                
                # Try pattern with double asterisks and max score
                overall_match = re.search(r'Overall Score[*\s]+\*\*(\d+\.?\d*)/(\d+)\*\*', line)
                if overall_match:
                    overall_score = float(overall_match.group(1))
                    max_score_val = int(overall_match.group(2))
                else:
                    # Try pattern with single asterisks and max score
                    overall_match = re.search(r'Overall Score[*\s]+\*(\d+\.?\d*)/(\d+)\*', line)
                    if overall_match:
                        overall_score = float(overall_match.group(1))
                        max_score_val = int(overall_match.group(2))
                    else:
                        # Try pattern with max score but no asterisks
                        overall_match = re.search(r'Overall Score[*\s]+(\d+\.?\d*)/(\d+)', line)
                        if overall_match:
                            overall_score = float(overall_match.group(1))
                            max_score_val = int(overall_match.group(2))
                        else:
                            # Try pattern without max score
                            overall_match = re.search(r'Overall Score[*\s]+(\d+\.?\d*)', line)
                            if overall_match:
                                overall_score = float(overall_match.group(1))
                            
                            # Also try pattern with double asterisks but no max score
                            if not overall_match:
                                overall_match = re.search(r'Overall Score[*\s]+\*\*(\d+\.?\d*)\*\*', line)
                                if overall_match:
                                    overall_score = float(overall_match.group(1))
                
                # Extract individual question scores
                q_scores = {}
                for q_num in range(1, 10):  # Support up to Q9
                    # Try numeric scores
                    q_match = re.search(rf'Q{q_num}:\s*(\d+\.?\d*)\*', line)
                    if q_match:
                        q_scores[f'q{q_num}'] = float(q_match.group(1))
                    else:
                        # Try Yes/No
                        yesno_match = re.search(rf'Q{q_num}:\s*(Yes|No)', line, re.IGNORECASE)
                        if yesno_match:
                            q_scores[f'q{q_num}'] = yesno_match.group(1)
                
                all_row_scores[row_num][run_idx] = {
                    'overall': overall_score,
                    'max_score': max_score_val,
                    'questions': q_scores
                }
    
    # Calculate averages and track raw scores for debugging
    averaged_scores = {}
    raw_scores_by_row = {}  # For debugging column
    
    for row_num, runs in all_row_scores.items():
        if not runs:
            continue
            
        overall_scores = [run['overall'] for run in runs.values()]
        avg_overall = sum(overall_scores) / len(overall_scores)
        max_score = runs[1]['max_score'] if 1 in runs else 15
        
        # Store raw overall scores for debugging
        raw_scores_by_row[row_num] = {'overall': overall_scores}
        
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
                # Store raw scores for this question
                raw_scores_by_row[row_num][q_key] = q_values
            else:
                avg_questions[q_key] = runs[1]['questions'].get(q_key, 'N/A')
                raw_scores_by_row[row_num][q_key] = [runs[1]['questions'].get(q_key, 'N/A')]
        
        averaged_scores[row_num] = {
            'overall': avg_overall,
            'max_score': max_score,
            'questions': avg_questions
        }
    
    # Rebuild analysis with averaged scores
    result_lines = []
    first_analysis_lines = analyses[0].split('\n')
    
    for line in first_analysis_lines:
        row_match = re.search(r'Row\s+(\d+)', line)
        if row_match and 'Overall Score' in line and row_match.group(1) in averaged_scores:
            row_num = row_match.group(1)
            scores = averaged_scores[row_num]
            
            reason_match = re.search(r'-\s*([^*\n]+?)(?:\*\*)?$', line)
            brief_reason = reason_match.group(1).strip() if reason_match else ''
            
            score_parts = []
            for q_key in sorted(scores['questions'].keys(), key=lambda x: int(re.search(r'\d+', x).group())):
                q_num = re.search(r'\d+', q_key).group()
                val = scores['questions'][q_key]
                if isinstance(val, (int, float)):
                    score_parts.append(f"Q{q_num}: {val:.2f}*")
                else:
                    score_parts.append(f"Q{q_num}: {val}")
            
            new_line = f"Row {row_num} - Overall Score **{scores['overall']:.2f}/{scores['max_score']}** - {' '.join(score_parts)} - {brief_reason}"
            result_lines.append(new_line)
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines), raw_scores_by_row

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
DEFAULT_SPREADSHEET_ID = "1jDJDQXPoZE6NTAqfTaCILv8ULXpM_vl5WeiEVSplChU"

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_spreadsheet(sheet_id=None):
    """Get authenticated spreadsheet connection"""
    # Try to get credentials from environment (Vercel/Production)
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    
    if creds_json:
        try:
            # Try to decode base64 first (Vercel format)
            try:
                decoded = base64.b64decode(creds_json).decode('utf-8')
                creds_dict = json.loads(decoded)
                print("Using base64-encoded Google credentials from environment variable")
            except:
                # Fall back to plain JSON
                creds_dict = json.loads(creds_json)
                print("Using plain JSON Google credentials from environment variable")
            
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        except Exception as e:
            print(f"Error parsing credentials from environment: {e}")
            raise
    else:
        # Use local file (development)
        creds = Credentials.from_service_account_file('google_credentials.json', scopes=SCOPES)
        print("Using Google credentials from local file")
    
    client = gspread.authorize(creds)
    spreadsheet_id = sheet_id or DEFAULT_SPREADSHEET_ID
    return client.open_by_key(spreadsheet_id)

def get_unanalyzed_applications(sheet_id=None, gid=None):
    """
    Get all applications that don't have analysis yet (column V is empty)
    Returns list of applications with row numbers
    """
    spreadsheet = get_spreadsheet(sheet_id)
    
    # Get worksheet by gid if provided, otherwise use first sheet
    if gid:
        try:
            # Find worksheet by gid
            worksheet = None
            for sheet in spreadsheet.worksheets():
                if str(sheet.id) == str(gid):
                    worksheet = sheet
                    break
            if not worksheet:
                print(f"Warning: Worksheet with gid={gid} not found, using first sheet")
                worksheet = spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"Error finding worksheet by gid: {e}, using first sheet")
            worksheet = spreadsheet.get_worksheet(0)
    else:
        worksheet = spreadsheet.get_worksheet(0)
    
    print(f"Using worksheet: {worksheet.title} (id: {worksheet.id})")
    
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

def column_index_to_letter(n):
    """Convert a 1-based column index to Excel column letter (1=A, 2=B, ..., 27=AA, etc.)"""
    result = ""
    while n > 0:
        n -= 1
        result = chr(65 + (n % 26)) + result
        n //= 26
    return result

def ensure_headers_exist(worksheet, question_count, start_col=22):
    """Ensure headers exist in row 1 for Overall Score, Q1-QN, and metadata columns"""
    try:
        all_values = worksheet.get_all_values()
        headers_row = all_values[0] if all_values else []
        
        # Build expected headers
        expected_headers = ['Overall Score']
        for q_num in range(1, question_count + 1):
            expected_headers.append(f'Q{q_num}')
        expected_headers.extend(['Brief Reason', 'Analyzed Date', 'Client', 'Job Description', 'Overall Score 1', 'Overall Score 2', 'Overall Score 3'])
        
        # Check if we need to add/update headers
        needs_update = False
        headers_to_write = []
        
        # Start at column V (22, 1-based)
        for i, header in enumerate(expected_headers):
            col_index_0based = start_col - 1 + i  # Convert start_col to 0-based, then add i
            col_index_1based = start_col + i  # For writing, use 1-based index
            if col_index_0based >= len(headers_row):
                # Need to extend headers row
                needs_update = True
                headers_to_write.append((col_index_1based, header))
            elif col_index_0based < len(headers_row) and headers_row[col_index_0based] != header:
                # Header exists but is different, update it
                needs_update = True
                headers_to_write.append((col_index_1based, header))
        
        if needs_update:
            # Update headers in batch
            for col_index, header in headers_to_write:
                col_letter = column_index_to_letter(col_index)
                worksheet.update(values=[[header]], range_name=f'{col_letter}1', value_input_option='USER_ENTERED')
            print(f"Updated headers for {len(headers_to_write)} columns starting at column {column_index_to_letter(start_col)}")
    except Exception as e:
        print(f"Warning: Could not ensure headers exist: {e}")

def analyze_and_write_to_sheet(selected_rows, client, job_description, supporting_references='', sheet_id=None, gid=None):
    """
    Analyze selected applications and write results back to the spreadsheet
    """
    spreadsheet = get_spreadsheet(sheet_id)
    
    # Get worksheet by gid if provided, otherwise use first sheet
    if gid:
        try:
            worksheet = None
            for sheet in spreadsheet.worksheets():
                if str(sheet.id) == str(gid):
                    worksheet = sheet
                    break
            if not worksheet:
                print(f"Warning: Worksheet with gid={gid} not found, using first sheet")
                worksheet = spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"Error finding worksheet by gid: {e}, using first sheet")
            worksheet = spreadsheet.get_worksheet(0)
    else:
        worksheet = spreadsheet.get_worksheet(0)
    
    print(f"Writing to worksheet: {worksheet.title} (id: {worksheet.id})")
    
    all_values = worksheet.get_all_values()
    
    # Build applications data for selected rows
    applications = []
    for row_num in selected_rows:
        row = all_values[row_num - 1]  # Convert to 0-indexed
        app = {
            'row_number': row_num,
            'sheet_id': sheet_id,
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
    
    # Get client criteria for dynamic scoring
    client_criteria = get_client_criteria_from_sheet(client, sheet_id)
    
    # Determine number of questions from client criteria
    question_count = 3  # default
    if isinstance(client_criteria, dict) and client_criteria:
        question_count = len(client_criteria)
    
    # Ensure headers exist in the spreadsheet
    ensure_headers_exist(worksheet, question_count, start_col=22)
    
    # Analyze with AI
    analysis_result = analyze_applications_ai(applications, client, job_description, supporting_references)
    
    if not analysis_result:
        return {'error': 'Analysis failed'}
    
    # Unpack analysis and raw scores
    analysis, raw_scores_by_row = analysis_result
    
    # Parse analysis and write to each row
    results = []
    failed_rows = []
    
    for app in applications:
        row_num = app['row_number']
        scores = extract_scores_for_row(analysis, row_num, all_values, client_criteria)
        
        if scores:
            try:
                # Start at column V (column 22, index 21)
                start_col = 22
                
                # Build values array: Overall Score, then all Q1-QN scores, then metadata
                # Ensure overall_score doesn't contain "/max_score" - strip it if present
                overall_score_value = scores.get('overall_score', '')
                if isinstance(overall_score_value, str) and '/' in overall_score_value:
                    overall_score_value = overall_score_value.split('/')[0].strip()
                
                values_row = [overall_score_value]
                
                # Add all question scores dynamically (Q1, Q2, Q3, Q4, Q5, Q6, Q7, etc.)
                for q_num in range(1, question_count + 1):
                    q_key = f'q{q_num}_score'
                    q_score = scores.get(q_key, 'N/A')
                    
                    # Check if it's a Yes/No answer (don't convert to star formula)
                    if q_score and q_score.upper() in ['YES', 'NO']:
                        values_row.append(q_score)
                    else:
                        # Extract numeric value for star formula (handles decimals)
                        q_num_val = q_score.replace('*', '') if q_score and q_score != 'N/A' else ''
                        
                        # Create formula for star rendering if it's a valid number (integer or decimal)
                        try:
                            # Try to convert to float to validate it's a number
                            float_val = float(q_num_val)
                            # For display, we'll show the decimal score as text since REPT only works with integers
                            # We can't use REPT with decimals, so just display the score with a star
                            q_formula = f'{q_num_val}*'
                        except (ValueError, TypeError):
                            q_formula = q_score
                        
                        values_row.append(q_formula)
                
                # Get the 3 individual overall scores for debugging
                # IMPORTANT: Only write numeric scores, never the old format
                row_num_str = str(row_num)
                overall_score_1 = ""
                overall_score_2 = ""
                overall_score_3 = ""
                
                if row_num_str in raw_scores_by_row:
                    raw = raw_scores_by_row[row_num_str]
                    if 'overall' in raw and isinstance(raw['overall'], list):
                        overall_list = raw['overall']
                        
                        # Filter out any non-numeric values
                        numeric_scores = [s for s in overall_list if isinstance(s, (int, float))]
                        
                        # Only write the first 3 numeric scores
                        if len(numeric_scores) >= 1:
                            overall_score_1 = f"{float(numeric_scores[0]):.2f}"
                        if len(numeric_scores) >= 2:
                            overall_score_2 = f"{float(numeric_scores[1]):.2f}"
                        if len(numeric_scores) >= 3:
                            overall_score_3 = f"{float(numeric_scores[2]):.2f}"
                    else:
                        print(f"Warning: Row {row_num} - 'overall' not found in raw_scores_by_row or is not a list")
                        print(f"  Available keys: {list(raw.keys()) if row_num_str in raw_scores_by_row else 'Row not found'}")
                else:
                    print(f"Warning: Row {row_num} not found in raw_scores_by_row")
                    print(f"  Available row numbers: {list(raw_scores_by_row.keys())}")
                
                # Add metadata columns
                values_row.extend([
                    scores.get('brief_reason', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    client,
                    job_description,
                    overall_score_1,  # Only numeric score, e.g., "10.00"
                    overall_score_2,  # Only numeric score, e.g., "10.50"
                    overall_score_3   # Only numeric score, e.g., "11.00"
                ])
                
                # Calculate end column (start_col + overall_score + question_count + metadata)
                # metadata: brief_reason, analyzed_date, client, job_description, overall_score_1, overall_score_2, overall_score_3 = 7 columns
                end_col = start_col + 1 + question_count + 7 - 1  # -1 because start_col is 1-based
                
                start_col_letter = column_index_to_letter(start_col)
                end_col_letter = column_index_to_letter(end_col)
                cell_range = f'{start_col_letter}{row_num}:{end_col_letter}{row_num}'
                
                # Use value_input_option='USER_ENTERED' to interpret formulas instead of text
                worksheet.update(values=[values_row], range_name=cell_range, value_input_option='USER_ENTERED')
                results.append({
                    'row': row_num,
                    'name': f"{app['first_name']} {app['surname']}",
                    'score': scores.get('overall_score', 'N/A')
                })
            except Exception as e:
                print(f"Error writing row {row_num}: {e}")
                import traceback
                traceback.print_exc()
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

def get_clients_list(sheet_id=None):
    """Get list of all clients from the Clients tab"""
    try:
        spreadsheet = get_spreadsheet(sheet_id)
        print(f"Getting clients from spreadsheet: {spreadsheet.title}")
        try:
            clients_worksheet = spreadsheet.worksheet('Clients')
            print(f"Found 'Clients' worksheet")
        except Exception as e:
            print(f"'Clients' tab not found: {e}")
            # Fallback to JSON if Clients tab doesn't exist
            try:
                with open('../ultils/clients.json', 'r') as f:
                    clients_data = json.load(f)
                    return [c['name'] for c in clients_data['clients']]
            except:
                return []
        
        all_values = clients_worksheet.get_all_values()
        print(f"Clients sheet has {len(all_values)} rows")
        print(f"Headers: {all_values[0] if all_values else 'None'}")
        
        if not all_values or len(all_values) < 2:
            print("No clients found (need at least header + 1 row)")
            return []
        
        # Extract full client data including criteria
        headers = all_values[0]
        clients = []
        
        for row in all_values[1:]:
            if row and row[0]:  # Skip empty rows
                client_name = row[0]
                criteria = {}
                
                # Extract criteria from remaining columns
                for i, header in enumerate(headers[1:], start=1):
                    if i < len(row) and row[i]:
                        criteria[header] = row[i]
                
                clients.append({
                    'name': client_name,
                    'criteria': criteria
                })
        
        print(f"Extracted {len(clients)} clients with criteria")
        return clients
    except Exception as e:
        print(f"Error getting clients list: {e}")
        import traceback
        traceback.print_exc()
        return []

def add_client_to_sheet(client_name, criteria_dict, sheet_id=None):
    """Add a new client with criteria to the Clients tab"""
    try:
        spreadsheet = get_spreadsheet(sheet_id)
        try:
            clients_worksheet = spreadsheet.worksheet('Clients')
        except:
            # Create the Clients worksheet if it doesn't exist
            clients_worksheet = spreadsheet.add_worksheet(title='Clients', rows=100, cols=20)
            # Add headers
            headers = ['Client Name', 'Question 1', 'Question 2', 'Question 3', 'Question 4', 
                       'Question 5', 'Question 6', 'Question 7']
            clients_worksheet.update(values=[headers], range_name='A1', value_input_option='USER_ENTERED')
        
        # Get current data to find next row
        all_values = clients_worksheet.get_all_values()
        next_row = len(all_values) + 1
        
        # Prepare row data
        headers = all_values[0] if all_values else ['Client Name']
        row_data = [client_name]
        
        # Add criteria in order of headers
        for header in headers[1:]:  # Skip 'Client Name'
            row_data.append(criteria_dict.get(header, ''))
        
        # Write the new client
        clients_worksheet.update(
            values=[row_data], 
            range_name=f'A{next_row}', 
            value_input_option='USER_ENTERED'
        )
        
        return {'success': True, 'message': f'Client "{client_name}" added successfully'}
    except Exception as e:
        print(f"Error adding client to sheet: {e}")
        return {'error': str(e)}

def delete_client_from_sheet(client_name, sheet_id=None):
    """Delete a client from the Clients tab"""
    try:
        spreadsheet = get_spreadsheet(sheet_id)
        try:
            clients_worksheet = spreadsheet.worksheet('Clients')
        except:
            return {'error': 'Clients tab not found'}
        
        all_values = clients_worksheet.get_all_values()
        if not all_values or len(all_values) < 2:
            return {'error': 'No clients found'}
        
        # Find the row with this client
        row_to_delete = None
        for idx, row in enumerate(all_values[1:], start=2):  # Start from row 2 (skip header)
            if row[0] == client_name:
                row_to_delete = idx
                break
        
        if not row_to_delete:
            return {'error': f'Client "{client_name}" not found'}
        
        # Delete the row
        clients_worksheet.delete_rows(row_to_delete)
        print(f"Deleted client '{client_name}' from row {row_to_delete}")
        
        return {'success': True, 'message': f'Client "{client_name}" deleted successfully'}
    except Exception as e:
        print(f"Error deleting client from sheet: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

def get_client_criteria_from_sheet(client_name, sheet_id=None):
    """Get client criteria from the Clients tab in Google Sheets"""
    try:
        spreadsheet = get_spreadsheet(sheet_id)
        # Try to get the Clients worksheet
        try:
            clients_worksheet = spreadsheet.worksheet('Clients')
        except:
            print("Warning: 'Clients' tab not found, falling back to JSON")
            return get_client_criteria_from_json(client_name)
        
        all_values = clients_worksheet.get_all_values()
        if not all_values:
            return None
        
        headers = all_values[0]
        
        # Find the row for this client
        for row in all_values[1:]:
            if row[0] == client_name:  # Assuming first column is Client Name
                criteria = {}
                for i, header in enumerate(headers[1:], start=1):  # Skip first column (Client Name)
                    if i < len(row) and row[i]:
                        criteria[header] = row[i]
                return criteria
        
        print(f"Warning: Client '{client_name}' not found in Clients tab")
        return None
    except Exception as e:
        print(f"Error reading from Clients sheet: {e}")
        return get_client_criteria_from_json(client_name)

def get_client_criteria_from_json(client_name):
    """Fallback: Load client criteria from JSON file"""
    try:
        with open('../ultils/clients.json', 'r') as f:
            clients_data = json.load(f)
            for c in clients_data['clients']:
                if c['name'] == client_name:
                    return c.get('Criteria', {})
    except Exception as e:
        print(f"Warning: Could not load client criteria from JSON: {e}")
    return None

def analyze_applications_ai(applications, client, job_description, supporting_references=''):
    """Analyze applications using OpenAI"""
    
    # Load client criteria from Google Sheets (with JSON fallback)
    sheet_id = applications[0].get('sheet_id') if applications else None
    client_criteria = get_client_criteria_from_sheet(client, sheet_id)
    
    criteria_text = ""
    if isinstance(client_criteria, dict):
        for question_num, criteria in client_criteria.items():
            criteria_text += f"\n{question_num}:\n{criteria}\n"
    else:
        criteria_text = client_criteria if client_criteria else 'No specific criteria provided'
    
    supporting_text = f"\n\nSupporting References:\n{supporting_references}" if supporting_references else ""
    
    # Format applications with row numbers - include Yes/No fields
    apps_formatted = []
    for app in applications:
        app_data = {
            'Row': app['row_number'],
            'Name': f"{app['first_name']} {app['surname']}",
            'University': app['university'],
            'Course': app['course'],
            'Right_to_work_UK': app.get('right_to_work', ''),
            'Visa_sponsorship_required': app.get('visa_sponsorship', ''),
            'GCSE_Maths_grade': app.get('gcse_maths', ''),
            'Available_Sept_2026': app.get('available_sept_2026', ''),
            'Understanding_of_role': app.get('understanding_of_role', ''),
            'Why_EDF': app.get('why_edf', ''),
            'What_stands_out': app.get('what_stands_out', '')
        }
        apps_formatted.append(app_data)
    
    # Determine number of questions and format type
    question_count = 3  # default
    is_7_question_format = False
    if isinstance(client_criteria, dict) and client_criteria:
        question_count = len(client_criteria)
        # Check if it's a 7-question format (Graduate Scheme format)
        is_7_question_format = (question_count == 7) or ("Graduate" in client and question_count >= 7)
    
    # Build dynamic scoring criteria based on client criteria
    # IMPORTANT: Use the actual criteria from the Clients tab
    scoring_criteria = ""
    
    # Log what criteria we're using for verification
    print(f"\n{'='*80}")
    print(f"📋 CLIENT CRITERIA VERIFICATION for {client}")
    print(f"{'='*80}")
    if isinstance(client_criteria, dict) and client_criteria:
        print(f"✅ Loaded {len(client_criteria)} questions from Clients tab:")
        for q_num, q_criteria in sorted(client_criteria.items()):
            print(f"  {q_num}: {q_criteria[:150]}{'...' if len(q_criteria) > 150 else ''}")
        print(f"\n📊 How these criteria will be used:")
        if is_7_question_format:
            print(f"  - Q1, Q2, Q3, Q5: Yes/No questions (from application data)")
            print(f"  - Q4: Scored against '{client_criteria.get('Question 4', 'N/A')[:80]}...'")
            print(f"  - Q6: Scored against '{client_criteria.get('Question 6', 'N/A')[:80]}...'")
            print(f"  - Q7: Scored against '{client_criteria.get('Question 7', 'N/A')[:80]}...'")
        else:
            for i, (q_num, q_criteria) in enumerate(sorted(client_criteria.items()), start=1):
                print(f"  - Q{i}: Scored against '{q_criteria[:80]}...'")
    else:
        print(f"⚠️  No criteria found - using defaults")
    print(f"{'='*80}\n")
    
    if is_7_question_format:
        # 7-question format: Q1-Q3 and Q5 are Yes/No, Q4/Q6/Q7 are scored
        # Map client criteria to questions (Question 1, Question 2, etc. from Clients tab)
        q1_criteria = client_criteria.get('Question 1', '') if isinstance(client_criteria, dict) else ''
        q2_criteria = client_criteria.get('Question 2', '') if isinstance(client_criteria, dict) else ''
        q3_criteria = client_criteria.get('Question 3', '') if isinstance(client_criteria, dict) else ''
        q4_criteria = client_criteria.get('Question 4', '') if isinstance(client_criteria, dict) else ''
        q5_criteria = client_criteria.get('Question 5', '') if isinstance(client_criteria, dict) else ''
        q6_criteria = client_criteria.get('Question 6', '') if isinstance(client_criteria, dict) else ''
        q7_criteria = client_criteria.get('Question 7', '') if isinstance(client_criteria, dict) else ''
        
        # Build scoring criteria using ACTUAL criteria from Clients tab
        scoring_criteria = f"""- Q1: "{q1_criteria if q1_criteria else 'Right to work in the UK'}" (Yes/No - extract from Right_to_work_UK field)
- Q2: "{q2_criteria if q2_criteria else 'Visa sponsorship required'}" (Yes/No - extract from Visa_sponsorship_required field)
- Q3: "{q3_criteria if q3_criteria else 'GCSE Maths grade'}" (Yes/No - extract from GCSE_Maths_grade field)
- Q4: "{q4_criteria if q4_criteria else 'Understanding of role'}" (1.00-5.00 stars with 2 decimal places - score based on Understanding_of_role answer using this criteria: {q4_criteria})
- Q5: "{q5_criteria if q5_criteria else 'Available from September 2026'}" (Yes/No - extract from Available_Sept_2026 field)
- Q6: "{q6_criteria if q6_criteria else 'Why EDF Trading'}" (1.00-5.00 stars with 2 decimal places - score based on Why_EDF answer using this criteria: {q6_criteria})
- Q7: "{q7_criteria if q7_criteria else 'What stands out about position'}" (1.00-5.00 stars with 2 decimal places - score based on What_stands_out answer using this criteria: {q7_criteria})"""
        
        max_score = 15  # Only Q4, Q6, Q7 are scored (3 questions × 5 stars = 15)
        overall_score_text = "Calculate the OVERALL SCORE as the SUM of Q4, Q6, and Q7 only (max 15 stars). Express as a decimal with 2 decimal places. Q1, Q2, Q3, and Q5 are Yes/No informational questions."
        score_format = "Q1: Yes/No Q2: Yes/No Q3: Yes/No Q4: [X.XX]* Q5: Yes/No Q6: [X.XX]* Q7: [X.XX]*"
    elif isinstance(client_criteria, dict) and client_criteria:
        question_count = len(client_criteria)
        # Use actual criteria from Clients tab - map Question 1, Question 2, etc. to Q1, Q2, etc.
        for i, (question_num, criteria) in enumerate(client_criteria.items(), start=1):
            q_num = i  # Use sequential numbering (Q1, Q2, Q3...)
            scoring_criteria += f"- Q{q_num}: \"{criteria}\" (1.00-5.00 stars with 2 decimal places - score based on candidate's answer using this specific criteria)\n"
        
        # Use the actual number of questions from client criteria
        max_score = question_count * 5
        overall_score_text = f"Calculate the OVERALL SCORE as the SUM of all Q scores (max {max_score} stars). Express as a decimal with 2 decimal places."
        score_format = " ".join([f"Q{i+1}: [X.XX]*" for i in range(question_count)])
    else:
        # Fallback to default 3 questions
        scoring_criteria = """- Q1: "Understanding of role" (1.00-5.00 stars with 2 decimal places)
- Q2: "Why EDF Trading" (1.00-5.00 stars with 2 decimal places)  
- Q3: "What stands out about this position" (1.00-5.00 stars with 2 decimal places)"""
        max_score = 15
        overall_score_text = "Calculate the OVERALL SCORE as the SUM of Q1, Q2, and Q3 (max 15 stars). Express as a decimal with 2 decimal places."
        score_format = "Q1: [X.XX]* Q2: [X.XX]* Q3: [X.XX]*"

    prompt = f"""ANALYZE EACH APPLICATION INDIVIDUALLY FOR {client} USING ONLY THE CLIENT CRITERIA BELOW.

🚨 CRITICAL RULES - FOLLOW EXACTLY:
1. IGNORE the job description completely - DO NOT use it for scoring
2. IGNORE generic role understanding - ONLY use the specific client criteria
3. If client criteria are numbers like "234" or "23423", these are INVALID criteria
4. For INVALID criteria (numbers/gibberish), give 1 star per question MAXIMUM
5. DO NOT make assumptions about what criteria "should" be
6. ONLY score based on how well candidates address the EXACT client criteria provided
7. ANALYZE EACH CANDIDATE INDIVIDUALLY - give unique scores and reasoning for each
8. READ EACH CANDIDATE'S ACTUAL ANSWERS CAREFULLY - do not use generic responses

Job Description: {job_description}{supporting_text}

Number of Applications: {len(applications)}

Applications Data:
{json.dumps(apps_formatted, indent=2)}

🎯 MANDATORY CLIENT CRITERIA (SCORE ONLY ON THESE):
{criteria_text}

📊 SCORING RULES - USE THE EXACT CRITERIA ABOVE FOR EACH QUESTION:
{scoring_criteria}

🚨 CRITICAL: For each scored question (Q4, Q6, Q7 in 7-question format, or all Q1-QN in other formats), you MUST:
1. Read the candidate's answer for that specific question
2. Compare it against the EXACT criteria provided above for that question
3. Score 1.00-5.00 stars (with 2 decimal places) based on how well the candidate's answer addresses the SPECIFIC criteria for that question
4. USE DECIMAL SCORES (e.g., 3.25*, 4.75*, 2.50*) to provide nuanced differentiation between candidates
5. Do NOT use generic scoring - each question has its own specific criteria
6. If a question's criteria is missing or invalid, you MUST still score based on what criteria is provided

🚨 DECIMAL SCORING RANGES:
- 1.00-1.99* = Poor match to criteria
- 2.00-2.99* = Below average match to criteria
- 3.00-3.99* = Average match to criteria
- 4.00-4.99* = Good match to criteria
- 5.00* = Excellent match to criteria

🚨 SCORING EXAMPLES:
- If criteria is "234" (invalid number) → Score 1.00* (candidate can't address a number)
- If criteria is "Understanding of role" → Score 1.00-5.00* based on how well they explain role understanding
- If criteria is gibberish → Score 1.00* (candidate can't address gibberish)

CRITICAL: {overall_score_text}
DO NOT use job description. DO NOT use generic analysis. ONLY use the client criteria above.
ALL SCORES MUST BE DECIMAL VALUES WITH 2 DECIMAL PLACES (e.g., 3.25*, 4.75*, 13.50/15).

🚨 INDIVIDUAL ANALYSIS REQUIREMENTS:
- READ each candidate's specific answers carefully
- Score 1.00-5.00* with 2 decimal places based on their ACTUAL responses, not generic templates
- Give DIFFERENT scores for DIFFERENT answers using decimal precision
- If a candidate gives a short answer, score accordingly (e.g., 2.25*, 2.75*)
- If a candidate gives a detailed answer, score accordingly (e.g., 4.25*, 4.75*)
- If a candidate gives a generic answer, score low (e.g., 2.00-2.50*)
- If a candidate gives a specific answer, score higher (e.g., 4.00-5.00*)

🚨 UNIQUENESS CHECK - BEFORE SUBMITTING YOUR ANALYSIS:
- Review ALL your brief reasons - if any 2 are similar, REWRITE them to be unique
- Each candidate should have DIFFERENT wording, DIFFERENT focus, DIFFERENT structure
- NO templates, NO copy-paste, NO generic phrases repeated across candidates
- Use casual language - contractions, informal words, conversational tone
- Avoid formal HR-speak like "demonstrates", "exhibits", "aligns with", "however"

{"FOR 7-QUESTION FORMAT (Graduate Scheme):" if is_7_question_format else ""}
{"- Q1, Q2, Q3, and Q5 are Yes/No questions - extract from Right_to_work_UK, Visa_sponsorship_required, GCSE_Maths_grade, and Available_Sept_2026 fields" if is_7_question_format else ""}
{"- ONLY Q4, Q6, and Q7 are scored (1.00-5.00 stars with 2 decimal places)" if is_7_question_format else ""}
{"- DO NOT use brackets around Yes/No answers (write 'Q1: Yes' not 'Q1: [Yes]')" if is_7_question_format else ""}
{"- DO NOT list Yes/No answers in brief reason - focus on Q4, Q6, Q7 content only" if is_7_question_format else ""}

For each candidate, provide the format EXACTLY as shown (USE DECIMAL SCORES with 2 decimal places):
"Row [row_number] - Overall Score **[X.XX]/{max_score}** - {score_format} - [brief reason]"

🚨 CRITICAL: The [brief reason] MUST be:
- Maximum 1-2 sentences (20-30 words total)
- Professional but simple - natural flow, NO question number mentions
- Examples:
  * "Has a solid grasp of the role, dives into quantitative aspects. Excited about the hands-on learning and ties in personal growth."
  * "Shows a general idea of the role but lacks depth. Drawn to the market position but could've tied in more specifics."

REMEMBER: ALL SCORES MUST BE DECIMAL WITH 2 DECIMAL PLACES (e.g., Q4: 3.75* Q6: 4.25* Q7: 4.50* - Overall Score **12.50/15**)
"""
    
    try:
        system_content = f"""You are an early careers recruiter analyzing applications for {client}. Write like you're texting a colleague, not writing a formal report.

🚨 CRITICAL RULES - VIOLATION WILL RESULT IN REJECTION:

1. EVERY CANDIDATE GETS A COMPLETELY DIFFERENT RESPONSE
   - If you write the same phrase for 2+ candidates, you FAILED
   - Each brief reason must be 100% unique - no copy-paste, no templates
   - Use different words, different structure, different focus for each candidate
   - Think: "What makes THIS candidate different from everyone else?"
   
2. WRITE CASUALLY - LIKE YOU'RE CHATTING WITH A COWORKER
   - Use contractions (they're, doesn't, hasn't)
   - Use casual phrases (kinda, sorta, pretty much, not really)
   - Avoid formal language (e.g., "demonstrates", "exhibits", "aligns with")
   - Write short, punchy observations, not essays
   - Examples:
     * BAD: "Candidate demonstrates a comprehensive understanding of the role"
     * GOOD: "Gets the role - talks about supporting traders and building models"
     * BAD: "Shows alignment with organizational values"  
     * GOOD: "Seems genuinely interested in energy markets, not just any internship"
   
3. READ EACH CANDIDATE'S ACTUAL ANSWERS - FIND WHAT'S UNIQUE
   - Role understanding: What specifically did THEY say? Not generic role stuff
   - Motivation: What specific reason did THEY give? Is it generic or personal?
   - What stands out: What caught THEIR eye? Be specific
   
4. BRIEF REASON FORMAT (THIS IS THE ONLY REASONING YOU PROVIDE):
   - MAXIMUM 1-2 SENTENCES (around 20-30 words total)
   - Natural flow: role understanding + motivation/interest
   - Professional but simple - like you're quickly summarizing to a colleague
   - DO NOT mention question numbers (no "Q1 was...", "Q4 shows...", "In Q6...")
   - Just flow naturally from one observation to the next
   - Examples:
     * PERFECT: "Has a solid grasp of the role, dives into quantitative aspects. Excited about the hands-on learning at EDFT and ties in personal growth with company values."
     * PERFECT: "Shows a general idea of the role but lacks depth. He's drawn to EDFT's market position but could've tied in more specifics about the role."
     * PERFECT: "Good grasp of the role, mentions analytical skills and programming. Really digs the culture and structure of the internship."
     * BAD (mentions questions): "Q4 shows understanding. Q6 reveals motivation. Q7 is strong."
     * BAD (too long): "Gets into the depth of EDF's role in energy and mentions practical experience, which is great. Shows a clear desire to contribute to EDF's goals, not just personal gain."
   - This is the ONLY analysis text you provide - no separate detailed section
   
5. EXAMPLES OF GOOD VS BAD:

   BAD (too formal, generic, could apply to anyone):
   "Candidate shows a general understanding of the role, mentioning support for traders and analysts. However, the response lacks depth regarding EDF Trading's position."
   
   PERFECT (natural flow, no question mentions):
   "Has a solid grasp of the role, dives into quantitative aspects. Excited about the hands-on learning and ties in personal growth with company values."
   
   PERFECT (professional but simple):
   "Shows a general idea of the role but lacks depth. Drawn to the market position but could've tied in more specifics about the role."
   
   BAD (mentions question numbers):
   "Q4 shows solid understanding. Q6 reveals genuine interest. Q7 is decent though - at least talks about learning vs contributing."
   
   BAD (way too long):
   "Mentions data modeling and trader support but pretty surface-level. Just wants to 'apply their skills' - not much substance. Answer is decent though - at least talks about learning vs contributing."
   
   BAD (formal and wordy):
   "Candidate demonstrates understanding of role requirements and expresses interest in the position. Response could benefit from more specific examples."
   
6. FORBIDDEN PHRASES/PATTERNS:
   - "Candidate shows/demonstrates/exhibits"
   - "However, the response lacks depth"
   - "aligns with", "demonstrates alignment"  
   - "could benefit from", "would be enhanced by"
   - Mentioning question numbers: "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "In Q4...", "Q6 shows..."
   - Any phrase that appears in 2+ candidate analyses
   - Writing more than 2 sentences (keep it SHORT!)
   
7. SCORING RULES:
   - Use ONLY the specific criteria from "🎯 MANDATORY CLIENT CRITERIA"
   - Each question has its own criteria - score against that specific criteria
   - Score from 1.00-5.00 with EXACTLY 2 decimal places (e.g., 3.75*, 4.25*, NOT 3* or 4*)
   - Use decimal precision to differentiate candidates (e.g., 3.25* vs 3.75*)
   - Be strict - most candidates won't hit all criteria perfectly
   
8. DECIMAL SCORING IS MANDATORY:
   - ALWAYS use 2 decimal places for ALL scores (e.g., 3.75*, NOT 3*)
   - Overall score must also have 2 decimals (e.g., 12.50/15, NOT 12/15)
   - Examples: Q4: 3.75* Q6: 4.25* Q7: 4.50* - Overall Score **12.50/15**"""
        
        if is_7_question_format:
            system_content += "\n\n9. FOR 7-QUESTION FORMAT:\n   - Q1-Q5 are already displayed separately\n   - Focus your brief reason on role understanding, motivation, and what stands out\n   - Maximum 1-2 sentences (20-30 words)\n   - Natural flow - DO NOT mention question numbers\n   - Example: 'Has a solid grasp of the role, dives into quantitative aspects. Excited about the hands-on learning and ties in personal growth.'\n   - Keep it professional but simple, and unique for each person\n   - REMEMBER: Score Q4, Q6, Q7 with 2 decimal places (e.g., 3.75*, 4.25*, 4.50*)"
        
        # Run analysis 3 times and average scores for consistency
        print(f"\n🔄 Running 3 analysis passes for {len(applications)} candidates to ensure scoring consistency...")
        analyses = []
        for run_num in range(1, 4):
            print(f"  📊 Analysis run {run_num}/3...")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0,
                top_p=1
            )
            analyses.append(response.choices[0].message.content)
        
        print("  ✅ Averaging scores from 3 runs...")
        analysis_text, raw_scores_by_row = average_analysis_scores_sheets(analyses)
        
        # Debug: Save a snippet of the analysis to see the format
        print(f"\n{'='*80}")
        print("📄 AI ANALYSIS OUTPUT (First 1000 chars):")
        print(f"{'='*80}")
        print(analysis_text[:1000])
        print(f"{'='*80}\n")
        
        return analysis_text, raw_scores_by_row
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return None, {}

def verify_client_criteria(client_name, sheet_id=None):
    """Verify and return the criteria being used for a specific client"""
    try:
        client_criteria = get_client_criteria_from_sheet(client_name, sheet_id)
        
        verification = {
            'client': client_name,
            'criteria_found': isinstance(client_criteria, dict) and len(client_criteria) > 0,
            'question_count': len(client_criteria) if isinstance(client_criteria, dict) else 0,
            'criteria': client_criteria,
            'source': 'Clients tab' if client_criteria else 'JSON fallback or default'
        }
        
        if isinstance(client_criteria, dict) and client_criteria:
            verification['questions'] = {}
            for q_num, q_criteria in sorted(client_criteria.items()):
                verification['questions'][q_num] = {
                    'criteria': q_criteria,
                    'length': len(q_criteria)
                }
        
        return verification
    except Exception as e:
        return {
            'client': client_name,
            'error': str(e),
            'criteria_found': False
        }

def extract_scores_for_row(analysis, row_number, all_values, client_criteria=None):
    """Extract scores from analysis for a specific row"""
    lines = analysis.split('\n')
    
    # Determine number of questions from client criteria
    question_count = 3  # default
    is_7_question_format = False
    if isinstance(client_criteria, dict) and client_criteria:
        question_count = len(client_criteria)
        # Check if it's a 7-question format (Graduate Scheme format)
        is_7_question_format = (question_count == 7)
    
    # Debug: Show all lines that contain "Overall Score" to see what format is being used
    print(f"\nDEBUG: Looking for Row {row_number} in analysis...")
    overall_score_lines = [line for line in lines if "Overall Score" in line]
    if overall_score_lines:
        print(f"DEBUG: Found {len(overall_score_lines)} lines with 'Overall Score':")
        for idx, line in enumerate(overall_score_lines[:5]):  # Show first 5
            print(f"  Line {idx}: {line[:200]}")
    else:
        print(f"DEBUG: No lines found with 'Overall Score' in analysis")
    
    for i, line in enumerate(lines):
        # Look for the row number in various formats
        row_patterns = [
            f"Row {row_number}",
            f"Row {row_number}:",
            f"Row {row_number} -",
            f"Row {row_number}.",
        ]
        
        if any(pattern in line for pattern in row_patterns) and "Overall Score" in line:
            # Extract overall score (dynamic max score)
            # For 7-question format, only Q4, Q6, Q7 are scored (max 15)
            # For other formats, all questions are scored (max question_count * 5)
            if is_7_question_format:
                max_score = 15  # Only Q4, Q6, Q7 are scored
            else:
                max_score = question_count * 5
            
            # Debug: print the line we're trying to parse
            print(f"DEBUG: Extracting overall score from line for Row {row_number}:")
            print(f"DEBUG: Line content: {line[:300]}")
            print(f"DEBUG: Looking for max_score={max_score}, is_7_question_format={is_7_question_format}")
            
            # Try multiple patterns to extract overall score (with decimal support)
            # Pattern 1: Decimal score with expected max_score and double asterisks (e.g., "Overall Score **13.50/15**")
            score_match = re.search(rf'Overall Score\s+\*\*(\d+\.?\d*)/{max_score}\*\*', line)
            
            # Pattern 2: Decimal score with expected max_score and single asterisk (e.g., "Overall Score *13.50/15*")
            if not score_match:
                score_match = re.search(rf'Overall Score\s+\*(\d+\.?\d*)/{max_score}\*', line)
            
            # Pattern 3: Decimal score with expected max_score no asterisks (e.g., "Overall Score 13.50/15")
            if not score_match:
                score_match = re.search(rf'Overall Score\s+(\d+\.?\d*)/{max_score}', line)
            
            # Pattern 4: Any decimal score pattern with double asterisks (e.g., "Overall Score **13.50/15**")
            if not score_match:
                score_match = re.search(r'Overall Score\s+\*\*(\d+\.?\d*)/(\d+)\*\*', line)
            
            # Pattern 5: Any decimal score pattern (X.XX/Y) as fallback
            if not score_match:
                fallback_match = re.search(r'Overall Score\s+\*?\*?(\d+\.?\d*)/(\d+)', line)
                if fallback_match:
                    actual_score = fallback_match.group(1)
                    actual_max = fallback_match.group(2)
                    print(f"Warning: Overall score format mismatch for Row {row_number}. Expected {max_score}, found {actual_max}. Using score: {actual_score}")
                    # Create a match object-like structure
                    class MatchObj:
                        def __init__(self, score):
                            self.group = lambda n: score if n == 1 else None
                    score_match = MatchObj(actual_score)
            
            # Pattern 6: Try to extract just the decimal number after Overall Score (e.g., "Overall Score **13.50**")
            if not score_match:
                simple_match = re.search(r'Overall Score\s+\*\*(\d+\.?\d*)\*\*', line)
                if simple_match:
                    actual_score = simple_match.group(1)
                    print(f"Info: Extracted overall score {actual_score} for Row {row_number} (max score format not found, using {max_score})")
                    class MatchObj:
                        def __init__(self, score):
                            self.group = lambda n: score if n == 1 else None
                    score_match = MatchObj(actual_score)
            
            # Pattern 7: Try to extract just the decimal number (e.g., "Overall Score 13.50")
            if not score_match:
                simple_match = re.search(r'Overall Score\s+(\d+\.?\d*)', line)
                if simple_match:
                    actual_score = simple_match.group(1)
                    print(f"Info: Extracted overall score {actual_score} for Row {row_number} (max score format not found, using {max_score})")
                    class MatchObj:
                        def __init__(self, score):
                            self.group = lambda n: score if n == 1 else None
                    score_match = MatchObj(actual_score)
            
            # Extract individual question scores dynamically (with decimal support)
            question_scores = {}
            for q_num in range(1, question_count + 1):
                # Try to match decimal numeric score first (e.g., "Q1: 4.25*" or "Q1: 4*")
                q_match = re.search(rf'Q{q_num}:\s*(\d+\.?\d*)\*', line)
                if q_match:
                    question_scores[f'q{q_num}_score'] = f"{q_match.group(1)}*"
                else:
                    # Try to match Yes/No answers (e.g., "Q1: Yes" or "Q1: No")
                    yesno_match = re.search(rf'Q{q_num}:\s*(Yes|No)', line, re.IGNORECASE)
                    if yesno_match:
                        question_scores[f'q{q_num}_score'] = yesno_match.group(1)
                    else:
                        question_scores[f'q{q_num}_score'] = 'N/A'
            
            reason_match = re.search(r'-\s*([^*\n]+?)(?:\*\*)?$', line)
            
            # Build result with dynamic question scores
            overall_score_str = 'N/A'
            if score_match:
                try:
                    score_value = score_match.group(1)
                    # Strip out any "/max_score" pattern that might be included
                    # Also handle cases where the value might be "10.00/15" instead of just "10.00"
                    if '/' in str(score_value):
                        score_value = str(score_value).split('/')[0]
                    # Just show the score value without "/max_score"
                    overall_score_str = score_value.strip()
                except Exception as e:
                    print(f"Error extracting overall score for Row {row_number}: {e}")
                    print(f"Line content: {line[:200]}")
                    overall_score_str = 'N/A'
            else:
                # Debug: print the line that should contain the score
                print(f"DEBUG: Could not extract overall score for Row {row_number}")
                print(f"DEBUG: Looking for max_score={max_score}, is_7_question_format={is_7_question_format}")
                print(f"DEBUG: Line content: {line[:200]}")
            
            result = {
                'overall_score': overall_score_str,
                'brief_reason': reason_match.group(1).strip() if reason_match else 'N/A'
            }
            
            # Add all question scores dynamically
            for q_num in range(1, question_count + 1):
                result[f'q{q_num}_score'] = question_scores.get(f'q{q_num}_score', 'N/A')
            
            return result
    
    return None

if __name__ == "__main__":
    # Test getting unanalyzed applications
    print("Testing get_unanalyzed_applications()...")
    apps = get_unanalyzed_applications()
    print(f"\nFound {len(apps)} unanalyzed applications:")
    for app in apps[:5]:  # Show first 5
        print(f"  Row {app['row_number']}: {app['first_name']} {app['surname']} - {app['university']}")

