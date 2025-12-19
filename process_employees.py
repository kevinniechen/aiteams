#!/usr/bin/env python3
"""
Process company employee data from PeopleDataLabs
Usage: python process_employees.py <company_slug> <linkedin_id> <website> [founding_date]

The founding_date (YYYY-MM format) filters out employees who "started" before 
the company existed (data quality issues). If not provided, no date filtering is applied.

Examples:
  python process_employees.py cognition cognition-ai-labs cognition.ai 2023-11
  python process_employees.py scale scaleai scale.com 2016-06
  python process_employees.py perplexity perplexity-ai perplexity.ai 2022-08
"""

import json
import sys
from datetime import datetime

CURRENT_YEAR = datetime.now().year

# Degree abbreviations
DEGREE_MAP = {
    'bachelor of science': 'BS',
    'bachelor of arts': 'BA',
    'bachelor of engineering': 'BE',
    'bachelor of business administration': 'BBA',
    'bachelor of fine arts': 'BFA',
    'bachelor of technology': 'BTech',
    'bachelors': 'BS',
    'master of science': 'MS',
    'master of arts': 'MA',
    'master of engineering': 'MEng',
    'master of business administration': 'MBA',
    'masters': 'MS',
    'doctor of philosophy': 'PhD',
    'doctorates': 'PhD',
    'juris doctor': 'JD',
}

# Major abbreviations
MAJOR_MAP = {
    'computer science': 'CS',
    'electrical engineering': 'EE',
    'mechanical engineering': 'ME',
    'computer engineering': 'CE',
    'mathematics': 'Math',
    'applied mathematics': 'Applied Math',
    'economics': 'Econ',
    'business administration': 'Business',
    'finance': 'Finance',
    'statistics': 'Stats',
    'physics': 'Physics',
    'data science': 'Data Science',
    'artificial intelligence': 'AI',
    'machine learning': 'ML',
}

# School abbreviations
SCHOOL_MAP = {
    'massachusetts institute of technology': 'MIT',
    'stanford university': 'Stanford',
    'harvard university': 'Harvard',
    'university of california, berkeley': 'UC Berkeley',
    'california institute of technology': 'Caltech',
    'carnegie mellon university': 'CMU',
    'university of california, los angeles': 'UCLA',
    'new york university': 'NYU',
    'university of southern california': 'USC',
    'university of pennsylvania': 'UPenn',
    'cornell university': 'Cornell',
    'princeton university': 'Princeton',
    'yale university': 'Yale',
    'columbia university': 'Columbia',
    'university of michigan': 'UMich',
    'university of illinois urbana - champaign': 'UIUC',
    'georgia institute of technology': 'Georgia Tech',
    'university of washington': 'UW',
    'university of texas at austin': 'UT Austin',
    'indian institute of technology, madras': 'IIT Madras',
    'indian institute of technology': 'IIT',
}

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

def abbreviate(text, mapping):
    """Abbreviate text using mapping, case-insensitive"""
    if not text:
        return None
    text_lower = text.lower()
    for full, abbrev in mapping.items():
        if full in text_lower:
            return abbrev
    return text.title()[:20]  # Truncate long names

def is_target_company(company, linkedin_id, website):
    """Check if a company matches our target"""
    company_linkedin = (company.get('linkedin_url') or '').lower()
    company_website = (company.get('website') or '').lower()
    
    return (linkedin_id in company_linkedin or website in company_website)

def is_founder_title(title):
    """Check if title indicates a founder role"""
    if not title:
        return False
    title_lower = title.lower()
    return 'founder' in title_lower or 'cofounder' in title_lower

def get_company_start_date(person, linkedin_id, website, founding_date):
    """Get the earliest start date at target company for a person"""
    earliest = None
    is_founder = False
    
    for exp in person.get('experience', []):
        company = exp.get('company', {})
        
        if is_target_company(company, linkedin_id, website):
            title = exp.get('title', {})
            title_name = title.get('name', '') if isinstance(title, dict) else str(title)
            if is_founder_title(title_name):
                is_founder = True
            
            start_date = exp.get('start_date')
            if start_date:
                parsed = parse_date(start_date)
                # Don't filter out founders even if start date is before founding date
                if founding_date and parsed < founding_date and not is_founder:
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

def get_previous_job(person, linkedin_id, website):
    """Get the title and company immediately before target company"""
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
            company_name = company.get('name', 'Unknown')
            if isinstance(title, dict):
                title_name = title.get('name', 'N/A')
            else:
                title_name = title or 'N/A'
            return title_name, company_name
    
    return "N/A", "N/A"

def get_first_job_year(person):
    """Get the year of the first job as a proxy for graduation"""
    experiences = person.get('experience', [])
    earliest_year = None
    
    for exp in experiences:
        start_date = exp.get('start_date')
        if start_date and len(start_date) >= 4:
            try:
                year = int(start_date[:4])
                if 1980 < year < 2030:
                    if earliest_year is None or year < earliest_year:
                        earliest_year = year
            except:
                pass
    
    return earliest_year

def get_bachelors_grad_year(person):
    """
    Get bachelor's graduation year with fallbacks:
    1. Actual bachelor's graduation year (use LATEST valid one to handle bad data)
    2. Year before grad school started (if no bachelor's found)
    3. First job start year (assume graduated same year)
    """
    education = person.get('education', [])
    
    bachelors_years = []  # Collect all valid bachelor's years
    earliest_grad_school_start = None
    
    for edu in education:
        degrees = edu.get('degrees', [])
        end_date = edu.get('end_date')
        start_date = edu.get('start_date')
        
        grad_year = None
        if end_date and len(end_date) >= 4:
            try:
                grad_year = int(end_date[:4])
            except:
                pass
        
        start_year = None
        if start_date and len(start_date) >= 4:
            try:
                start_year = int(start_date[:4])
            except:
                pass
        
        for degree in degrees:
            degree_lower = degree.lower()
            # Check for bachelor's
            if 'bachelor' in degree_lower or degree_lower == 'bachelors':
                if grad_year and 1980 < grad_year < 2030:
                    bachelors_years.append(grad_year)
                break
            # Check for grad school (master's, PhD, MBA, JD)
            if any(g in degree_lower for g in ['master', 'doctor', 'phd', 'mba', 'juris']):
                if start_year and 1980 < start_year < 2030:
                    if earliest_grad_school_start is None or start_year < earliest_grad_school_start:
                        earliest_grad_school_start = start_year
    
    # Priority 1: Use the LATEST bachelor's year (to filter out bad old data)
    if bachelors_years:
        return max(bachelors_years), False
    
    # Priority 2: Year before grad school started
    if earliest_grad_school_start:
        return earliest_grad_school_start - 1, True
    
    # Priority 3: First job year
    first_job_year = get_first_job_year(person)
    if first_job_year:
        return first_job_year, True
    
    return None, False

def get_education_formatted(person):
    """Get formatted education like 'BS CS, MIT '16' """
    education = person.get('education', [])
    if not education:
        return None, None
    
    bachelors_edu = None
    highest_edu = None
    bachelors_year = None
    
    for edu in education:
        degrees = edu.get('degrees', [])
        end_date = edu.get('end_date')
        
        grad_year = None
        if end_date:
            if len(end_date) >= 4:
                try:
                    grad_year = int(end_date[:4])
                except:
                    pass
        
        for degree in degrees:
            degree_lower = degree.lower()
            if 'bachelor' in degree_lower or degree_lower == 'bachelors':
                bachelors_edu = edu
                bachelors_year = grad_year
                break
        
        if highest_edu is None:
            highest_edu = edu
    
    display_edu = highest_edu or bachelors_edu
    if not display_edu:
        display_edu = education[0]
    
    school = display_edu.get('school', {})
    school_name = school.get('name', '') if isinstance(school, dict) else str(school)
    degrees = display_edu.get('degrees', [])
    majors = display_edu.get('majors', [])
    end_date = display_edu.get('end_date')
    
    degree_abbrev = None
    if degrees:
        degree_abbrev = abbreviate(degrees[0], DEGREE_MAP)
    
    major_abbrev = None
    if majors:
        major_abbrev = abbreviate(majors[0], MAJOR_MAP)
    
    school_abbrev = abbreviate(school_name, SCHOOL_MAP) if school_name else None
    
    year_str = None
    if end_date and len(end_date) >= 4:
        try:
            year = int(end_date[:4])
            if 1980 < year < 2030:
                year_str = f"'{str(year)[2:]}"
        except:
            pass
    
    parts = []
    if degree_abbrev and major_abbrev:
        parts.append(f"{degree_abbrev} {major_abbrev}")
    elif degree_abbrev:
        parts.append(degree_abbrev)
    elif major_abbrev:
        parts.append(major_abbrev)
    
    if school_abbrev:
        if year_str:
            parts.append(f"{school_abbrev} {year_str}")
        else:
            parts.append(school_abbrev)
    
    formatted = ", ".join(parts) if parts else None
    
    return formatted, bachelors_year

def get_age(person, bachelors_year, yoe=None):
    """Calculate age from birth_year, bachelor's graduation, or YoE. Always returns an age."""
    birth_year = person.get('birth_year')
    
    # Priority 1: Actual birth year
    if birth_year and isinstance(birth_year, int) and 1950 < birth_year < 2010:
        return CURRENT_YEAR - birth_year, False
    
    # Priority 2: Bachelor's graduation (assume graduated at 22)
    if bachelors_year and isinstance(bachelors_year, int) and 1980 < bachelors_year < 2030:
        estimated_birth = bachelors_year - 22
        return CURRENT_YEAR - estimated_birth, True
    
    # Priority 3: YoE (assume started working at 22)
    if yoe and isinstance(yoe, (int, float)) and yoe > 0:
        return 22 + int(yoe), True
    
    # Priority 4: Fallback - assume 30 years old
    return 30, True

def get_yoe(person, bachelors_year):
    """Get years of experience from bachelor's graduation year, first job, or PDL estimate"""
    # Priority 1: Bachelor's graduation year
    if bachelors_year and isinstance(bachelors_year, int) and 1980 < bachelors_year < 2030:
        return CURRENT_YEAR - bachelors_year
    
    # Priority 2: First job year (assume started working right after college)
    first_job_year = get_first_job_year(person)
    if first_job_year:
        return CURRENT_YEAR - first_job_year
    
    # Priority 3: PDL's estimate
    yoe = person.get('inferred_years_experience')
    if yoe and isinstance(yoe, (int, float)):
        return int(yoe)
    
    return None

def get_linkedin_url(person):
    """Get LinkedIn URL"""
    url = person.get('linkedin_url')
    if url:
        if not url.startswith('http'):
            return f"https://{url}"
        return url
    return None

def main():
    if len(sys.argv) < 4:
        print("Usage: python process_employees.py <company_slug> <linkedin_id> <website> [founding_date]")
        print()
        print("founding_date is optional (YYYY-MM format). If provided, filters out employees")
        print("with start dates before the company was founded (data quality filter).")
        print()
        print("Examples:")
        print("  python process_employees.py cognition cognition-ai-labs cognition.ai 2023-11")
        print("  python process_employees.py scale scaleai scale.com 2016-06")
        print("  python process_employees.py perplexity perplexity-ai perplexity.ai 2022-08")
        sys.exit(1)
    
    company_slug = sys.argv[1]
    linkedin_id = sys.argv[2]
    website = sys.argv[3]
    
    founding_date = None
    founding_date_str = None
    if len(sys.argv) >= 5:
        founding_date_str = sys.argv[4]
        founding_date = parse_date(founding_date_str)
    
    input_file = f"{company_slug}_employees_raw.json"
    output_txt = f"{company_slug}_earliest_employees.txt"
    output_json = f"{company_slug}_processed.json"
    
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found. Run query_pdl.py first.")
        sys.exit(1)
    
    employees = data.get('data', [])
    print(f"Total employees found: {len(employees)}")
    print(f"Company: {company_slug} (LinkedIn: {linkedin_id}, Website: {website})")
    if founding_date:
        print(f"Founding date filter: {founding_date.strftime('%Y-%m')} (excluding earlier dates)")
    else:
        print("Founding date filter: None (no date filtering)")
    print()
    
    valid_employees = []
    for emp in employees:
        start_date = get_company_start_date(emp, linkedin_id, website, founding_date)
        if start_date != datetime.max:
            valid_employees.append((emp, start_date))
    
    sorted_employees = sorted(valid_employees, key=lambda x: x[1])
    
    print(f"Employees with valid start dates: {len(sorted_employees)}")
    print("=" * 100)
    print()
    
    # Build output data
    output_lines = []
    output_lines.append(f"{company_slug.upper()} - EARLIEST EMPLOYEES")
    if founding_date:
        output_lines.append(f"(Founded: {founding_date.strftime('%Y-%m')})")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    json_data = {
        "company": company_slug,
        "company_display": company_slug.title(),
        "founded": founding_date_str,
        "employees": []
    }
    
    for i, (emp, start_date) in enumerate(sorted_employees[:100], 1):
        name = emp.get('full_name', 'Unknown').title()
        title = get_company_title(emp, linkedin_id, website).title()
        prev_title, prev_company = get_previous_job(emp, linkedin_id, website)
        prev_title = prev_title.title()
        prev_company = prev_company.title()
        edu_formatted, _ = get_education_formatted(emp)
        grad_year, grad_estimated = get_bachelors_grad_year(emp)
        yoe = get_yoe(emp, grad_year)
        age, is_estimated = get_age(emp, grad_year, yoe)
        linkedin_url = get_linkedin_url(emp)
        start_str = start_date.strftime("%Y-%m")
        
        # Format grad year as '16 style (no tilde for estimates)
        if grad_year:
            grad_year_str = f"'{str(grad_year)[2:]}"
        else:
            grad_year_str = "?"
        
        age_str = f"~{age}" if is_estimated else str(age)
        yoe_str = str(yoe) if yoe else "?"
        edu_str = edu_formatted if edu_formatted else "N/A"
        
        print(f"Employee #{i}")
        print(f"  Name: {name}")
        print(f"  Age: {age_str} | YoE: {yoe_str}")
        print(f"  Start Date: {start_str}")
        print(f"  Title: {title}")
        print(f"  Previous: {prev_title} @ {prev_company}")
        print(f"  Education: {edu_str}")
        if linkedin_url:
            print(f"  LinkedIn: {linkedin_url}")
        print()
        
        output_lines.append(f"Employee #{i}")
        output_lines.append(f"  Name: {name}")
        output_lines.append(f"  Grad: {grad_year_str} | YoE: {yoe_str}")
        output_lines.append(f"  Start Date: {start_str}")
        output_lines.append(f"  Title: {title}")
        output_lines.append(f"  Previous: {prev_title} @ {prev_company}")
        output_lines.append(f"  Education: {edu_str}")
        if linkedin_url:
            output_lines.append(f"  LinkedIn: {linkedin_url}")
        output_lines.append("")
        
        # Add to JSON
        json_data["employees"].append({
            "rank": i,
            "name": name,
            "grad_year": grad_year_str,
            "yoe": yoe_str,
            "start_date": start_str,
            "title": title,
            "previous_title": prev_title,
            "previous_company": prev_company,
            "education": edu_str,
            "linkedin_url": linkedin_url
        })
    
    with open(output_txt, "w") as f:
        f.write("\n".join(output_lines))
    
    with open(output_json, "w") as f:
        json.dump(json_data, f, indent=2)
    
    print("=" * 100)
    print(f"Results saved to {output_txt} and {output_json}")

if __name__ == "__main__":
    main()
