#!/usr/bin/env python3
"""
Build script to generate a static version of the AI Teams site.
- Inlines all company JSON data into the HTML
- Removes delete/spam buttons and functionality
- Outputs to docs/ folder for GitHub Pages / Vercel deployment
"""

import json
import os
import re
from pathlib import Path

def build_static():
    # Read the original index.html
    with open('index.html', 'r') as f:
        html = f.read()
    
    # Read all company data files based on what's in the COMPANIES array
    companies = [
        'perplexity', 'cognition', 'cursor', 'elevenlabs', 'physical-intelligence',
        'harvey', 'sierra', 'glean', 'saronic', 'decagon', 'contextual',
        'distyl', 'serval', 'brainco', 'augment', 'manus', 'anthropic'
    ]
    
    company_data = {}
    for company in companies:
        filename = f'{company}_processed.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                company_data[company] = json.load(f)
    
    # Read raises data
    raises_data = {}
    if os.path.exists('raises.json'):
        with open('raises.json', 'r') as f:
            raises_data = json.load(f)
    
    # Read spam data
    spam_data = {}
    if os.path.exists('spam.json'):
        with open('spam.json', 'r') as f:
            spam_data = json.load(f)
    
    # Read manual additions and merge into company data
    if os.path.exists('manual_additions.json'):
        with open('manual_additions.json', 'r') as f:
            manual_data = json.load(f)
        
        manual_count = 0
        for company_slug, employees in manual_data.items():
            if company_slug.startswith('_'):  # Skip comments
                continue
            if company_slug in company_data:
                existing_names = {e['name'].lower() for e in company_data[company_slug].get('employees', [])}
                for emp in employees:
                    if emp['name'].lower() not in existing_names:
                        emp_entry = {
                            'rank': 0,
                            'name': emp['name'],
                            'grad_year': emp.get('grad_year', '?'),
                            'yoe': emp.get('yoe', '?'),
                            'start_date': emp['start_date'],
                            'title': emp.get('title', 'N/A'),
                            'original_title': emp.get('title', 'N/A'),
                            'previous_title': emp.get('previous_title', 'N/A'),
                            'previous_company': emp.get('previous_company', 'N/A'),
                            'previous_title_2': emp.get('previous_title_2', 'N/A'),
                            'previous_company_2': emp.get('previous_company_2', 'N/A'),
                            'education': emp.get('education', 'N/A'),
                            'linkedin_url': emp.get('linkedin_url')
                        }
                        company_data[company_slug]['employees'].append(emp_entry)
                        manual_count += 1
                
                # Re-sort by start_date and re-rank
                company_data[company_slug]['employees'].sort(key=lambda x: x['start_date'])
                for i, emp in enumerate(company_data[company_slug]['employees']):
                    emp['rank'] = i + 1
        
        if manual_count > 0:
            print(f"  - Added {manual_count} manual entries from manual_additions.json")
    
    # Create inline data script
    inline_data = f'''
    <script>
        // Inlined data for static site
        const PRELOADED_DATA = {json.dumps(company_data)};
        const PRELOADED_RAISES = {json.dumps(raises_data)};
        const PRELOADED_SPAM = {json.dumps(spam_data)};
    </script>
    '''
    
    # Inject inline data before the main script
    html = html.replace('<script>', inline_data + '\n    <script>', 1)
    
    # Replace the entire loadData function with static version
    new_load = '''async function loadData() {
            // Static site: use preloaded data
            companyData = PRELOADED_DATA;
            raisesData = PRELOADED_RAISES;
            spamData = PRELOADED_SPAM;
            
            renderTabs();
            const first = Object.keys(companyData)[0];
            if (first) showCompany(first);
            else document.getElementById('content').textContent = 'No data found.';
        }'''
    
    # Use regex to replace the loadData function
    html = re.sub(
        r'async function loadData\(\) \{[\s\S]*?renderTabs\(\);\s*const first = Object\.keys\(companyData\)\[0\];\s*if \(first\) showCompany\(first\);\s*else document\.getElementById\(\'content\'\)\.textContent = \'No data found\.\';\s*\}',
        new_load,
        html
    )
    
    # Remove the spam button column header (the empty th for action column)
    html = re.sub(r'<th class="col-action"></th>', '', html)
    
    # Remove the spam button td from table rows
    html = re.sub(
        r'<td class="col-action"><button class="spam-btn"[^>]*>×</button></td>',
        '',
        html
    )
    
    # Remove col-action CSS
    html = re.sub(r'\.col-action \{[^}]+\}', '', html)
    
    # Remove spam-btn CSS
    html = re.sub(r'\.spam-btn \{[^}]+\}', '', html)
    
    # Remove toggleSpam function completely
    # Match: async function toggleSpam(company, name) { ... entire function body ... }
    toggleSpam_pattern = r'async function toggleSpam\(company, name\) \{\s*const wasSpam = isSpam\(company, name\);[\s\S]*?alert\(\'Failed to save spam status\'\);\s*\}\s*\}'
    html = re.sub(toggleSpam_pattern, '// toggleSpam removed in static build', html)
    
    # Remove "(X hidden)" text from company info
    html = re.sub(r"\$\{spamCount > 0 \? ` \(\$\{spamCount\} hidden\)` : ''\}", "", html)
    
    # Create docs folder
    os.makedirs('docs', exist_ok=True)
    
    # Write static HTML
    with open('docs/index.html', 'w') as f:
        f.write(html)
    
    print(f"✓ Built static site to docs/index.html")
    print(f"  - Inlined {len(company_data)} company datasets")
    print(f"  - Inlined spam list ({sum(len(v) for v in spam_data.values())} entries)")
    print(f"  - Removed X buttons")
    print(f"  - Ready for deployment")

if __name__ == '__main__':
    build_static()
