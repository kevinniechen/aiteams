#!/usr/bin/env python3
"""
Query PeopleDataLabs for company employees - fetches earliest employees by year
Usage: python query_pdl.py <company_slug> <linkedin_company_id> <founding_year> [end_year]

Queries year by year from founding_year up to end_year (inclusive).
If end_year not provided, queries until 100+ total records or hits current year.
WARNING: If any single year has >100 results, you'll only get a random 100 from that year.

Examples:
  python query_pdl.py harvey harvey-ai 2022 2023    # Only 2022-2023 (safe)
  python query_pdl.py cognition cognition-ai-labs 2023 2024
"""

import requests
import json
import sys
from datetime import datetime

# API Configuration
API_KEY = '56e5282049cc8dbb438df598d36ec28ce76ccd5310610eab46af2dc653447854'
PDL_URL = "https://api.peopledatalabs.com/v5/person/search"

HEADERS = {
    'Content-Type': "application/json",
    'X-api-key': API_KEY
}

def query_year(linkedin_id, year):
    """Query PDL for employees who started in a specific year"""
    sql_query = f"""
        SELECT * FROM person 
        WHERE job_company_linkedin_url='linkedin.com/company/{linkedin_id}' 
        AND job_start_date >= '{year}-01-01'
        AND job_start_date < '{year + 1}-01-01'
    """
    
    params = {
        'sql': sql_query,
        'size': 100,
        'pretty': True
    }
    
    print(f"  Querying year {year}...")
    response = requests.get(PDL_URL, headers=HEADERS, params=params)
    result = response.json()
    
    if response.status_code == 200 and result.get("status") == 200:
        data = result.get('data', [])
        total = result.get('total', len(data))
        print(f"    Found {len(data)} records (total available: {total})")
        if total > 100:
            print(f"    ⚠️  WARNING: {total} total but only got 100 - results may be incomplete!")
        return data, total
    else:
        print(f"    Error: {response.status_code}")
        print(f"    {result.get('error', {}).get('message', 'Unknown error')}")
        return [], 0

def query_company(company_slug, linkedin_id, founding_year, end_year=None):
    """Query PDL for earliest employees of a company"""
    
    current_year = datetime.now().year
    
    print(f"Querying PeopleDataLabs for {company_slug} employees...")
    print(f"LinkedIn ID: {linkedin_id}")
    print(f"Founding year: {founding_year}")
    if end_year:
        print(f"End year: {end_year}")
    print()
    
    all_data = []
    year = founding_year
    
    while True:
        # Stop if we've passed end_year (if specified) or current year
        if end_year and year > end_year:
            break
        if year > current_year:
            break
            
        year_data, year_total = query_year(linkedin_id, year)
        all_data.extend(year_data)
        
        # If no end_year specified, stop once we have 100+ records
        if not end_year and len(all_data) >= 100:
            break
            
        year += 1
    
    output_file = f"{company_slug}_employees_raw.json"
    
    # Wrap in same format as original API response
    result = {
        "status": 200,
        "data": all_data,
        "total": len(all_data)
    }
    
    with open(output_file, "w") as out:
        json.dump(result, out, indent=2)
    
    print()
    print(f"Total records retrieved: {len(all_data)}")
    print(f"Results saved to {output_file}")

def main():
    if len(sys.argv) < 4:
        print("Usage: python query_pdl.py <company_slug> <linkedin_company_id> <founding_year> [end_year]")
        print()
        print("Examples:")
        print("  python query_pdl.py harvey harvey-ai 2022 2023    # Only 2022-2023")
        print("  python query_pdl.py cognition cognition-ai-labs 2023 2024")
        print()
        print("If end_year is provided, queries all years from founding to end (inclusive).")
        print("If end_year is omitted, queries until 100+ total records are found.")
        sys.exit(1)
    
    company_slug = sys.argv[1]
    linkedin_id = sys.argv[2]
    founding_year = int(sys.argv[3])
    end_year = int(sys.argv[4]) if len(sys.argv) >= 5 else None
    
    query_company(company_slug, linkedin_id, founding_year, end_year)

if __name__ == "__main__":
    main()
