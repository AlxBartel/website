#!/usr/bin/env python3
"""
arXiv Author Paper Fetcher
Generates a static HTML page with recent papers by specified authors.
All papers are combined into a single list, sorted by last updated date.
Run this script periodically to update the HTML file.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from html import escape

# CONFIGURATION: Add your author identifiers here
AUTHORS = [
    {
        'name': 'Alex Bartel',
        'id': 'bartel_a_1',
        'type': 'arxiv'  # 'arxiv' or 'orcid'
    },
    {
        'name': 'Ross Paterson',
        'id': 'paterson_r_1',
        'type': 'arxiv'  # 'arxiv' or 'orcid'
    },
    {
        'name': 'Dan Loughran',
        'id': '0000-0001-5892-1564',
        'type': 'orcid'  # 'arxiv' or 'orcid'
    },
    # Add more authors here as needed
]

# Maximum number of papers to show per author (before deduplication)
MAX_PAPERS_PER_AUTHOR = 20

# Output file path
OUTPUT_FILE = 'index.html'


def fetch_author_feed(author):
    """Fetch the Atom feed for an author."""
    if author['type'] == 'orcid':
        orcid_id = author['id'].replace('https://orcid.org/', '').replace('http://orcid.org/', '')
        feed_url = f"https://arxiv.org/a/{orcid_id}.atom2"
    else:
        feed_url = f"https://arxiv.org/a/{author['id']}.atom2"
    
    print(f"Fetching papers for {author['name']} from {feed_url}...")
    
    try:
        with urllib.request.urlopen(feed_url) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f"  Error: HTTP {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def parse_atom_feed(xml_text):
    """Parse the Atom feed XML and extract paper information."""
    papers = []
    
    try:
        root = ET.fromstring(xml_text)
        
        # Define namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}
        
        entries = root.findall('atom:entry', ns)
        
        for entry in entries[:MAX_PAPERS_PER_AUTHOR]:
            title = entry.find('atom:title', ns)
            summary = entry.find('atom:summary', ns)
            published = entry.find('atom:published', ns)
            updated = entry.find('atom:updated', ns)
            id_elem = entry.find('atom:id', ns)
            
            authors = [author.find('atom:name', ns).text 
                      for author in entry.findall('atom:author', ns)]
            
            categories = [cat.get('term') 
                         for cat in entry.findall('atom:category', ns)]
            
            # Extract arXiv ID from the URL
            arxiv_id = None
            if id_elem is not None:
                url = id_elem.text
                if '/abs/' in url:
                    arxiv_id = url.split('/abs/')[-1]
            
            if title is not None and id_elem is not None:
                papers.append({
                    'title': title.text.strip(),
                    'summary': summary.text.strip() if summary is not None else '',
                    'authors': authors,
                    'published': published.text if published is not None else '',
                    'updated': updated.text if updated is not None else '',
                    'url': id_elem.text,
                    'arxiv_id': arxiv_id,
                    'categories': categories[:3]
                })
        
        print(f"  Found {len(papers)} papers")
        return papers
    
    except Exception as e:
        print(f"  Error parsing XML: {e}")
        return []


def format_date(date_string):
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y')
    except:
        return date_string


def generate_html(all_author_papers):
    """Generate the complete HTML page with all papers in a single list."""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>arXiv Author Papers</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #ffffff;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .paper {
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: box-shadow 0.2s;
        }
        
        .paper:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .paper-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        
        .paper-title a {
            color: #3498db;
            text-decoration: none;
        }
        
        .paper-title a:hover {
            text-decoration: underline;
        }
        
        .paper-authors {
            color: #555;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .paper-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #7f8c8d;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        
        .paper-abstract {
            color: #555;
            font-size: 14px;
            line-height: 1.6;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #f0f0f0;
        }
        
        .paper-abstract.collapsed {
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .show-more {
            color: #3498db;
            cursor: pointer;
            font-size: 13px;
            margin-top: 5px;
            display: inline-block;
        }
        
        .show-more:hover {
            text-decoration: underline;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-size: 16px;
        }
        
        .last-updated {
            text-align: center;
            color: #95a5a6;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Recent arXiv Papers</h1>
"""
    
    # Collect all papers from all authors into a single list
    all_papers = []
    seen_arxiv_ids = set()
    
    for author_data in all_author_papers:
        for paper in author_data['papers']:
            # Skip duplicates based on arXiv ID
            if paper['arxiv_id'] and paper['arxiv_id'] in seen_arxiv_ids:
                continue
            if paper['arxiv_id']:
                seen_arxiv_ids.add(paper['arxiv_id'])
            all_papers.append(paper)
    
    # Sort by updated date (most recent first)
    all_papers.sort(key=lambda p: p['updated'], reverse=True)
    
    # Generate HTML for all papers
    if not all_papers:
        html += """
        <div class="no-results">No papers found</div>
"""
    else:
        for idx, paper in enumerate(all_papers):
            abstract_id = f"abstract-{idx}"
            categories = ', '.join(paper['categories']) if paper['categories'] else ''
            
            html += f"""
        <div class="paper">
            <div class="paper-title">
                <a href="{escape(paper['url'])}" target="_blank" rel="noopener noreferrer">{escape(paper['title'])}</a>
            </div>
            <div class="paper-authors">
                {escape(', '.join(paper['authors']))}
            </div>
            <div class="paper-meta">
                <span>📅 {format_date(paper['published'])}</span>
"""
            
            if paper['arxiv_id']:
                html += f"""                <span>🔖 {escape(paper['arxiv_id'])}</span>
"""
            
            if categories:
                html += f"""                <span>🏷️ {escape(categories)}</span>
"""
            
            html += f"""            </div>
            <div class="paper-abstract collapsed" id="{abstract_id}">
                {escape(paper['summary'])}
            </div>
            <span class="show-more" onclick="toggleAbstract('{abstract_id}', this)">Show more</span>
        </div>
"""
    
    # Add footer with generation time and paper count
    now = datetime.now().strftime('%b %d, %Y at %I:%M %p')
    paper_count = len(all_papers)
    
    html += f"""
        <div class="last-updated">Generated: {now} | {paper_count} paper{'s' if paper_count != 1 else ''} displayed</div>
    </div>

    <script>
        function toggleAbstract(id, element) {{
            const abstract = document.getElementById(id);
            if (abstract.classList.contains('collapsed')) {{
                abstract.classList.remove('collapsed');
                element.textContent = 'Show less';
            }} else {{
                abstract.classList.add('collapsed');
                element.textContent = 'Show more';
            }}
        }}
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Main function to fetch papers and generate HTML."""
    print("arXiv Author Paper Fetcher")
    print("=" * 50)
    
    all_author_papers = []
    
    for author in AUTHORS:
        xml_data = fetch_author_feed(author)
        
        if xml_data:
            papers = parse_atom_feed(xml_data)
            all_author_papers.append({
                'author': author,
                'papers': papers
            })
        else:
            all_author_papers.append({
                'author': author,
                'papers': []
            })
    
    print("\nGenerating HTML...")
    html_content = generate_html(all_author_papers)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML file generated: {OUTPUT_FILE}")
    print(f"\nYou can now upload this file to your web hosting and embed it in Google Sites.")


if __name__ == '__main__':
    main()
