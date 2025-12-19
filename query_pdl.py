#!/usr/bin/env python3
"""
Query PeopleDataLabs for company employees - fetches earliest employees by year
Usage: python query_pdl.py <company_slug> <linkedin_company_id> <founding_year>

Examples:
  python query_pdl.py cognition cognition-ai-labs 2023
  python query_pdl.py scale scaleai 2016
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
        return data, total
    else:
        print(f"    Error: {response.status_code}")
        print(f"    {result.get('error', {}).get('message', 'Unknown error')}")
        return [], 0

def query_company(company_slug, linkedin_id, founding_year):
    """Query PDL for earliest employees of a company"""
    
    print(f"Querying PeopleDataLabs for {company_slug} employees...")
    print(f"LinkedIn ID: {linkedin_id}")
    print(f"Founding year: {founding_year}")
    print()
    
    all_data = []
    
    # Query first year
    year1_data, year1_total = query_year(linkedin_id, founding_year)
    all_data.extend(year1_data)
    
    # If first year has <100 results, also query second year
    if year1_total < 100:
        year2_data, year2_total = query_year(linkedin_id, founding_year + 1)
        all_data.extend(year2_data)
        
        # If still <100, query third year too
        if year1_total + year2_total < 100:
            year3_data, _ = query_year(linkedin_id, founding_year + 2)
            all_data.extend(year3_data)
    
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
        print("Usage: python query_pdl.py <company_slug> <linkedin_company_id> <founding_year>")
        print()
        print("Examples:")
        print("  python query_pdl.py cognition cognition-ai-labs 2023")
        print("  python query_pdl.py scale scaleai 2016")
        sys.exit(1)
    
    company_slug = sys.argv[1]
    linkedin_id = sys.argv[2]
    founding_year = int(sys.argv[3])
    
    query_company(company_slug, linkedin_id, founding_year)

if __name__ == "__main__":
    main()
