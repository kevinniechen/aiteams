#!/usr/bin/env python3
"""
Process company employee data from PeopleDataLabs
Usage: python process_employees.py <company_slug> <linkedin_id> <website> <founding_date>

Examples:
  python process_employees.py cognition cognition-ai-labs cognition.ai 2023-11
  python process_employees.py scale scaleai scale.com 2016-01
"""

import json
import sys
from datetime import datetime

def parse_date(date_str):
    """Parse date string in various formats to datetime for sorting"""
    if not date_str:
        return datetime.max
    
    if len(date_str) == 7:  # YYYY-MM
        return datetime.strptime(date_str, "%Y-%m")
    elif len(date_str) == 10:  # YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%d")
    elif len(date_str) == 4:  # YYYY
        return datetime.strptime(date_str, "%Y")
    else:
        return datetime.max

def is_target_company(company, linkedin_id, website):
    """Check if a company matches our target"""
    company_linkedin = (company.get('linkedin_url') or '').lower()
    company_website = (company.get('website') or '').lower()
    
    return (linkedin_id in company_linkedin or website in company_website)

def get_company_start_date(person, linkedin_id, website, founding_date):
    """Get the earliest start date at target company for a person"""
    earliest = None
    
    for exp in person.get('experience', []):
        company = exp.get('company', {})
        
        if is_target_company(company, linkedin_id, website):
            start_date = exp.get('start_date')
            if start_date:
                parsed = parse_date(start_date)
                # Filter out dates before founding (fraudulent data)
                if parsed < founding_date:
                    continue
                if earliest is None or parsed < earliest:
                    earliest = parsed
    
    return earliest if earliest else datetime.max

def get_company_title(person, linkedin_id, website):
    """Get current title at target company"""
    for exp in person.get('experience', []):
        company = exp.get('company', {})
        
        if is_target_company(company, linkedin_id, website):
            title = exp.get('title', {})
            if isinstance(title, dict):
                return title.get('name', 'N/A')
            return title or 'N/A'
    
    return person.get('job_title', 'N/A')

def get_previous_title(person, linkedin_id, website):
    """Get the title at the job immediately before target company"""
    experiences = person.get('experience', [])
    sorted_exp = sorted(experiences, key=lambda x: parse_date(x.get('start_date')), reverse=True)
    
    found_company = False
    for exp in sorted_exp:
        company = exp.get('company', {})
        
        if is_target_company(company, linkedin_id, website):
            found_company = True
            continue
        
        if found_company:
            title = exp.get('title', {})
            company_name_display = company.get('name', 'Unknown')
            if isinstance(title, dict):
                title_name = title.get('name', 'N/A')
            else:
                title_name = title or 'N/A'
            return f"{title_name} at {company_name_display}"
    
    return "N/A"

def get_education(person):
    """Get education details"""
    education = person.get('education', [])
    if not education:
        return "N/A"
    
    edu_list = []
    for edu in education[:2]:
        school = edu.get('school', {})
        school_name = school.get('name', 'Unknown') if isinstance(school, dict) else str(school)
        degrees = edu.get('degrees', [])
        majors = edu.get('majors', [])
        
        degree_str = degrees[0] if degrees else ""
        major_str = majors[0] if majors else ""
        
        if degree_str and major_str:
            edu_list.append(f"{degree_str} in {major_str} - {school_name}")
        elif degree_str:
            edu_list.append(f"{degree_str} - {school_name}")
        elif major_str:
            edu_list.append(f"{major_str} - {school_name}")
        else:
            edu_list.append(school_name)
    
    return "; ".join(edu_list)

def main():
    if len(sys.argv) < 5:
        print("Usage: python process_employees.py <company_slug> <linkedin_id> <website> <founding_date>")
        print()
        print("Examples:")
        print("  python process_employees.py cognition cognition-ai-labs cognition.ai 2023-11")
        print("  python process_employees.py scale scaleai scale.com 2016-01")
        sys.exit(1)
    
    company_slug = sys.argv[1]
    linkedin_id = sys.argv[2]
    website = sys.argv[3]
    founding_date = parse_date(sys.argv[4])
    
    input_file = f"{company_slug}_employees_raw.json"
    output_file = f"{company_slug}_earliest_employees.txt"
    
    # Load data
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found. Run query_pdl.py first.")
        sys.exit(1)
    
    employees = data.get('data', [])
    print(f"Total employees found: {len(employees)}")
    print(f"Company: {company_slug} (LinkedIn: {linkedin_id}, Website: {website})")
    print(f"Founding date filter: {founding_date.strftime('%Y-%m')}")
    print()
    
    # Filter and sort employees
    valid_employees = []
    for emp in employees:
        start_date = get_company_start_date(emp, linkedin_id, website, founding_date)
        if start_date != datetime.max:
            valid_employees.append((emp, start_date))
    
    sorted_employees = sorted(valid_employees, key=lambda x: x[1])
    
    print(f"Employees with valid start dates: {len(sorted_employees)}")
    print("=" * 100)
    print()
    
    # Output results
    output_lines = []
    output_lines.append(f"{company_slug.upper()} - EARLIEST EMPLOYEES")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    for i, (emp, start_date) in enumerate(sorted_employees[:30], 1):
        name = emp.get('full_name', 'Unknown').title()
        title = get_company_title(emp, linkedin_id, website)
        prev_title = get_previous_title(emp, linkedin_id, website)
        education = get_education(emp)
        start_str = start_date.strftime("%Y-%m")
        
        print(f"Employee #{i}")
        print(f"  Name: {name}")
        print(f"  Start Date: {start_str}")
        print(f"  Title: {title}")
        print(f"  Previous Title: {prev_title}")
        print(f"  Education: {education}")
        print()
        
        output_lines.append(f"Employee #{i}")
        output_lines.append(f"  Name: {name}")
        output_lines.append(f"  Start Date: {start_str}")
        output_lines.append(f"  Title: {title}")
        output_lines.append(f"  Previous Title: {prev_title}")
        output_lines.append(f"  Education: {education}")
        output_lines.append("")
    
    with open(output_file, "w") as f:
        f.write("\n".join(output_lines))
    
    print("=" * 100)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
