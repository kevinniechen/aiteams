#!/usr/bin/env python3
"""
Query PeopleDataLabs for company employees
Usage: python query_pdl.py <company_slug> <linkedin_company_id>

Examples:
  python query_pdl.py cognition cognition-ai-labs
  python query_pdl.py scale scaleai
"""

import requests
import json
import sys

# API Configuration
API_KEY = '56e5282049cc8dbb438df598d36ec28ce76ccd5310610eab46af2dc653447854'
PDL_URL = "https://api.peopledatalabs.com/v5/person/search"

HEADERS = {
    'Content-Type': "application/json",
    'X-api-key': API_KEY
}

def query_company(company_slug, linkedin_id):
    """Query PDL for employees of a company"""
    
    # SQL Query for company employees who started before 2025
    sql_query = f"""
        SELECT * FROM person 
        WHERE job_company_linkedin_url='linkedin.com/company/{linkedin_id}' 
        AND job_start_date < '2025'
    """
    
    params = {
        'sql': sql_query,
        'size': 100,
        'pretty': True
    }
    
    print(f"Querying PeopleDataLabs for {company_slug} employees...")
    print(f"LinkedIn ID: {linkedin_id}")
    print(f"Query: {sql_query.strip()}")
    print()
    
    response = requests.get(PDL_URL, headers=HEADERS, params=params)
    result = response.json()
    
    output_file = f"{company_slug}_employees_raw.json"
    
    if response.status_code == 200 and result.get("status") == 200:
        data = result.get('data', [])
        total = result.get('total', len(data))
        
        with open(output_file, "w") as out:
            json.dump(result, out, indent=2)
        
        print(f"Successfully retrieved {len(data)} records (total available: {total})")
        print(f"Results saved to {output_file}")
    else:
        print(f"Error: {response.status_code}")
        print(json.dumps(result, indent=2))
        
        with open(output_file, "w") as out:
            json.dump(result, out, indent=2)

def main():
    if len(sys.argv) < 3:
        print("Usage: python query_pdl.py <company_slug> <linkedin_company_id>")
        print()
        print("Examples:")
        print("  python query_pdl.py cognition cognition-ai-labs")
        print("  python query_pdl.py scale scaleai")
        sys.exit(1)
    
    company_slug = sys.argv[1]
    linkedin_id = sys.argv[2]
    
    query_company(company_slug, linkedin_id)

if __name__ == "__main__":
    main()
