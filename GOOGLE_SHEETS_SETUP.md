# Google Sheets Integration Setup

This guide will help you set up the Google Sheets integration to automatically analyze job applications.

## How It Works

1. Form submissions go to your Google Sheet (tab 1)
2. Run the analyzer script
3. AI analyzes all applications
4. Results are written to a new "AI Analysis" tab with scores and reasoning

## Setup Steps

### Step 1: Create Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Give it a name (e.g., "sheets-analyzer")
   - Click "Create and Continue"
   - Skip the optional steps, click "Done"

5. Create and Download Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Click "Create" - this downloads the credentials file

6. Save the credentials file:
   ```bash
   # Move the downloaded file to your backend folder and rename it
   mv ~/Downloads/your-project-name-*.json backend/google_credentials.json
   ```

### Step 2: Share Your Spreadsheet

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1jDJDQXPoZE6NTAqfTaCILv8ULXpM_vl5WeiEVSplChU/edit

2. Click "Share" button

3. Find the service account email in your credentials file:
   - Open `backend/google_credentials.json`
   - Look for `"client_email"`: something like `sheets-analyzer@project-name.iam.gserviceaccount.com`
   - Copy this email

4. Add the service account email to your spreadsheet with "Editor" permissions

### Step 3: Verify Your Sheet Structure

Your spreadsheet should have these columns (in order):
1. Form_ID
2. University
3. Course
4. Please upload your CV
5. Do you have the right to work in the UK?
6. Do you require visa sponsorship?
7. Do you have at least a grade C or above/grade 4 or above in GCSE Maths?
8. Are you available from September 2026?
9. What is your understanding of this role based on the job description?
10. Why do you want to work for EDF Trading?
11. What is it about this Graduate position that stands out for you?
12. Would you like to create a Higherin.com account to hear about similar opportunities?
13. For information on how we process your data, here is a link to the privacy statement.
14. Registration Date

### Step 4: Run the Analyzer

```bash
cd backend
python3 sheets_processor.py
```

The script will:
1. ✅ Connect to your Google Sheet
2. ✅ Read all applications from the first tab
3. ✅ Analyze each application with AI
4. ✅ Create/update an "AI Analysis" tab with results

### Output Format

The "AI Analysis" tab will contain:

| Form_ID | University | Course | Overall_Score | Q4_Understanding | Q6_Why_EDF | Q7_What_Stands_Out | Brief_Reason | Detailed_Reasoning | Analyzed_Date |
|---------|------------|--------|---------------|------------------|------------|-----------------------|--------------|-------------------|---------------|
| 001     | Cambridge  | Econ   | 13/15         | 4*               | 4*         | 5*                    | Strong...    | User 001: ...     | 2025-10-08... |

### Column Descriptions

- **Form_ID**: Unique identifier from the form
- **University**: Applicant's university
- **Course**: Applicant's course of study
- **Overall_Score**: Sum of Q4 + Q6 + Q7 (max 15/15)
- **Q4_Understanding**: Score for understanding of role (1-5*)
- **Q6_Why_EDF**: Score for motivation to work at EDF (1-5*)
- **Q7_What_Stands_Out**: Score for what appeals about the position (1-5*)
- **Brief_Reason**: One-line summary of assessment
- **Detailed_Reasoning**: In-depth explanation of scores
- **Analyzed_Date**: When the analysis was performed

## Troubleshooting

### Error: "Could not connect to Google Sheets"
- Check that `google_credentials.json` is in the `backend/` folder
- Verify the Google Sheets API is enabled in Google Cloud Console
- Make sure you shared the spreadsheet with the service account email

### Error: "No applications to process"
- Check that your spreadsheet has data in the first worksheet
- Verify the Form_ID column (first column) has values

### Error: "OpenAI API error"
- Check your `OPENAI_API_KEY` in `backend/.env`
- Make sure you have API credits available

## Running Automatically

You can set up a cron job or schedule to run this automatically:

```bash
# Run every hour
0 * * * * cd /path/to/Sifting-tool/backend && python3 sheets_processor.py

# Run every day at 9 AM
0 9 * * * cd /path/to/Sifting-tool/backend && python3 sheets_processor.py
```

## API Costs

Approximate OpenAI costs:
- Small applications (< 500 words): ~$0.01 per analysis
- Medium applications (500-1000 words): ~$0.02 per analysis
- Large applications (> 1000 words): ~$0.03 per analysis

For 50 applications: approximately $0.50 - $1.50 per run

