#!/usr/bin/env python3
"""
Build script to generate a static version of the AI Teams site.
- Inlines all company JSON data into the HTML
- Removes delete/spam buttons and functionality
- Outputs to docs/ folder for GitHub Pages deployment
"""

import json
import os
import re
import shutil
from pathlib import Path

def build_static():
    # Read the original index.html
    with open('index.html', 'r') as f:
        html = f.read()
    
    # Read all company data files
    companies = [
        'perplexity', 'cognition', 'harvey', 'sierra', 'decagon',
        'glean', 'distyl', 'cursor', 'peregrine', 'physical-intelligence',
        'serval', 'brainco', 'elevenlabs', 'contextual', 'saronic'
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
    
    # Create inline data script
    inline_data = f'''
    <script>
        // Inlined data for static site
        const PRELOADED_DATA = {json.dumps(company_data)};
        const PRELOADED_RAISES = {json.dumps(raises_data)};
    </script>
    '''
    
    # Inject inline data before the main script
    html = html.replace('<script>', inline_data + '\n    <script>', 1)
    
    # Modify loadData to use preloaded data instead of fetch
    old_load = '''async function loadData() {
            try {
                const spamRes = await fetch('/spam.json');
                if (spamRes.ok) spamData = await spamRes.json();
            } catch (e) {}
            
            try {
                const raisesRes = await fetch('/raises.json');
                if (raisesRes.ok) raisesData = await raisesRes.json();
            } catch (e) {}
            
            for (const company of COMPANIES) {
                try {
                    const response = await fetch(company.file);
                    if (response.ok) {
                        companyData[company.slug] = await response.json();
                    }
                } catch (e) {}
            }
            renderTabs();
            const first = Object.keys(companyData)[0];
            if (first) showCompany(first);
            else document.getElementById('content').textContent = 'No data found.';
        }'''
    
    new_load = '''async function loadData() {
            // Static site: use preloaded data
            companyData = PRELOADED_DATA;
            raisesData = PRELOADED_RAISES;
            spamData = {}; // No spam filtering in static site
            
            renderTabs();
            const first = Object.keys(companyData)[0];
            if (first) showCompany(first);
            else document.getElementById('content').textContent = 'No data found.';
        }'''
    
    html = html.replace(old_load, new_load)
    
    # Remove the spam button column header
    html = html.replace('<th></th>', '')
    
    # Remove the spam button from table rows - replace the entire td with button
    html = re.sub(
        r"<td><button class=\"spam-btn\" onclick=\"toggleSpam\([^)]+\)\">×</button></td>",
        '',
        html
    )
    
    # Remove toggleSpam function (it won't be called anyway but cleaner to remove)
    old_toggle = '''async function toggleSpam(company, name) {
            const wasSpam = isSpam(company, name);
            
            try {
                await fetch('/spam', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company, name, is_spam: !wasSpam })
                });
                
                if (!spamData[company]) spamData[company] = [];
                if (wasSpam) {
                    spamData[company] = spamData[company].filter(n => n !== name);
                } else {
                    spamData[company].push(name);
                }
                
                showCompany(currentCompany);
            } catch (e) {
                alert('Failed to save spam status');
            }
        }'''
    
    html = html.replace(old_toggle, '// toggleSpam removed in static build')
    
    # Remove spam button CSS
    html = html.replace('.spam-btn { cursor: pointer; padding: 2px 8px; font-size: 11px; }', '')
    
    # Create docs folder for GitHub Pages
    os.makedirs('docs', exist_ok=True)
    
    # Write static HTML
    with open('docs/index.html', 'w') as f:
        f.write(html)
    
    print(f"✓ Built static site to docs/index.html")
    print(f"  - Inlined {len(company_data)} company datasets")
    print(f"  - Removed spam/delete functionality")
    print(f"  - Ready for GitHub Pages deployment")

if __name__ == '__main__':
    build_static()
