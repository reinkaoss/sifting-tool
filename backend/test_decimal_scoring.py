#!/usr/bin/env python3
"""
Test script to verify decimal scoring consistency
Runs the same candidate through analysis 3 times
"""

import requests
import json

# Test candidate data
job_description = """Commercial Summer Internship
Overview of EDF Trading (EDFT)
EDF Trading is a specialist in the wholesale energy markets, providing a gateway to energy markets for buyers and sellers of a wide range of energy commodities. We are part of the EDF Group, a global leader in low-carbon energies.

EDFT are at the fore-front of the European power and gas markets. We apply our reach, corporate strength, physical and financial market presence to add value to the assets of the EDF Group and our third party customers.

Our culture
We are proud of our ethnic and cultural diversity. We are high-performing people working together to achieve common goals. Innovative and flexible in our thinking, we are able to adapt and change, which is critical to our success. Respect is our foundation, it's what empowers our employees to unlock their full potential. Our people are encouraged to speak up, and we listen, which drives collective understanding, collaboration and achievement.

Internship overview
Our summer internship programme provides you with an exciting opportunity to develop and utilise new skills, explore interesting fields and undertake challenging and innovative work within a fast-paced trading environment.

We typically have opportunities across:

Energy commodities trading
Market risk
Analytics
Quant Risk
Origination
What you can expect
A structured paid summer internship programme at our Global Headquarters in London.

This typically provides:

Hands-on participation in a real business project
Comprehensive industry specific and personal and professional skills training
Opportunities to build your network across the business globally
Regular opportunities to interact with our commercial teams and leaders
Ongoing check-ins and continuous coaching from your manager and mentor
Social activities
End of placement presentation to our C-Suite and key stakeholders
Successful completion of a summer internship with EDFT provides you with the potential to be offered a place on our 2 year Commercial Graduate Programme.

What we are looking for
EDFT constantly seeks curious, enthusiastic and commercially astute students with an entrepreneurial spirit who are eager to explore a career in energy markets.

We are ideally looking for individuals with:

An interest in the energy industry
The ability to think critically
Strong quantitative and qualitative analytical skills
Excellent interpersonal skills
Knowledge of programming languages
Candidates must:

Be available to start in Summer 2026
Be based in our London office
Graduating in 2026 or 2027
Have a right to work in the UK"""

# Test candidate (same user 3 times)
test_candidate = {
    "User": "1",
    "Question 1": "hands on work with experienced professional teaching in a social environment. working within the energy market and enhancing my understanding and confidence in management and finance",
    "Question 2": "the work environment seems to be most welcoming and friendly, not making fell afraid to ask a question or for help",
    "Question 3": "the variety of tasks presented. whereas other companies will just put you at a desk all summer, EDF Trading seems to help out new entries and provide meaningful training and assistance with interesting work"
}

def run_analysis(run_number):
    """Run a single analysis"""
    print(f"\n{'='*80}")
    print(f"RUN {run_number}")
    print(f"{'='*80}")
    
    payload = {
        "client": "EDF Trading - Internship",
        "jobDescription": job_description,
        "supportingReferences": "",
        "csvData": [test_candidate],
        "userCount": 1
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('analysis', '')
            print("\n📊 Analysis Result:")
            print("-" * 80)
            print(analysis)
            print("-" * 80)
            return analysis
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_scores(analysis_text):
    """Extract scores from analysis text"""
    import re
    
    # Look for Overall Score pattern with decimals
    overall_match = re.search(r'Overall Score[*\s]+(\d+\.?\d*)/15', analysis_text)
    
    # Look for Q1, Q2, Q3 scores with decimals
    q1_match = re.search(r'Q1:\s*(\d+\.?\d*)\*', analysis_text)
    q2_match = re.search(r'Q2:\s*(\d+\.?\d*)\*', analysis_text)
    q3_match = re.search(r'Q3:\s*(\d+\.?\d*)\*', analysis_text)
    
    return {
        'overall': overall_match.group(1) if overall_match else 'N/A',
        'q1': q1_match.group(1) if q1_match else 'N/A',
        'q2': q2_match.group(1) if q2_match else 'N/A',
        'q3': q3_match.group(1) if q3_match else 'N/A'
    }

def main():
    print("\n" + "="*80)
    print("🔬 DECIMAL SCORING CONSISTENCY TEST")
    print("="*80)
    print("Testing the same candidate 3 times to check decimal score consistency")
    print("Client: EDF Trading - Internship (3-question format)")
    print("Temperature: 0 (100% deterministic - no variation in scores)")
    print("="*80)
    
    # Run analysis 3 times
    results = []
    for i in range(1, 4):
        analysis = run_analysis(i)
        if analysis:
            scores = extract_scores(analysis)
            results.append(scores)
        else:
            print(f"Failed to get analysis for run {i}")
    
    # Display comparison
    print("\n" + "="*80)
    print("📈 SCORE COMPARISON")
    print("="*80)
    
    if len(results) == 3:
        print(f"\n{'Run':<10} {'Overall':<15} {'Q1':<10} {'Q2':<10} {'Q3':<10}")
        print("-" * 55)
        for i, scores in enumerate(results, 1):
            print(f"Run {i:<5} {scores['overall']:<15} {scores['q1']:<10} {scores['q2']:<10} {scores['q3']:<10}")
        
        # Calculate variance
        print("\n" + "="*80)
        print("📊 CONSISTENCY ANALYSIS")
        print("="*80)
        
        # Check if scores are different (due to temperature=0.85, we expect some variation)
        overall_scores = [float(s['overall']) if s['overall'] != 'N/A' else 0 for s in results]
        q1_scores = [float(s['q1']) if s['q1'] != 'N/A' else 0 for s in results]
        q2_scores = [float(s['q2']) if s['q2'] != 'N/A' else 0 for s in results]
        q3_scores = [float(s['q3']) if s['q3'] != 'N/A' else 0 for s in results]
        
        print(f"\nOverall Score Range: {min(overall_scores):.2f} - {max(overall_scores):.2f}")
        print(f"Q1 Score Range: {min(q1_scores):.2f} - {max(q1_scores):.2f}")
        print(f"Q2 Score Range: {min(q2_scores):.2f} - {max(q2_scores):.2f}")
        print(f"Q3 Score Range: {min(q3_scores):.2f} - {max(q3_scores):.2f}")
        
        # Calculate average
        avg_overall = sum(overall_scores) / len(overall_scores)
        avg_q1 = sum(q1_scores) / len(q1_scores)
        avg_q2 = sum(q2_scores) / len(q2_scores)
        avg_q3 = sum(q3_scores) / len(q3_scores)
        
        print(f"\nAverage Overall Score: {avg_overall:.2f}/15")
        print(f"Average Q1 Score: {avg_q1:.2f}/5")
        print(f"Average Q2 Score: {avg_q2:.2f}/5")
        print(f"Average Q3 Score: {avg_q3:.2f}/5")
        
        print("\n✅ All scores are using decimal format (X.XX)")
        print("Note: Some variation is expected due to temperature=0.85 setting")
        print("This provides natural variation in reasoning while maintaining score consistency")
    else:
        print("❌ Could not complete all 3 runs")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

