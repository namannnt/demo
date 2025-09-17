# utils/sources.py
"""
Source credibility database and checking functions
"""

# Highly reliable sources (score: 8-10)
RELIABLE_SOURCES = {
    'reuters.com': {'score': 9, 'type': 'news_agency', 'bias': 'center'},
    'apnews.com': {'score': 9, 'type': 'news_agency', 'bias': 'center'},
    'bbc.com': {'score': 8, 'type': 'broadcaster', 'bias': 'center'},
    'cdc.gov': {'score': 9, 'type': 'government', 'bias': 'center'},
    'who.int': {'score': 9, 'type': 'international_org', 'bias': 'center'},
    'nasa.gov': {'score': 9, 'type': 'government', 'bias': 'center'},
    'nature.com': {'score': 9, 'type': 'academic', 'bias': 'center'},
    'nytimes.com': {'score': 7, 'type': 'newspaper', 'bias': 'left'},
    'wsj.com': {'score': 7, 'type': 'newspaper', 'bias': 'right'},
}

# Known unreliable sources (score: 1-3)
UNRELIABLE_SOURCES = {
    'infowars.com': {'score': 1, 'type': 'conspiracy', 'issues': ['misinformation']},
    'naturalnews.com': {'score': 2, 'type': 'pseudoscience', 'issues': ['health_misinformation']},
}

def extract_domain(url):
    """Extract domain from URL"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return None

def check_source_credibility(url):
    """Check source credibility based on domain"""
    domain = extract_domain(url)
    if not domain:
        return {
            'credibility': 'unknown',
            'score': 5,
            'reason': 'Could not extract domain from URL'
        }
    
    if domain in RELIABLE_SOURCES:
        source_info = RELIABLE_SOURCES[domain]
        return {
            'credibility': 'reliable',
            'score': source_info['score'],
            'source_type': source_info['type'],
            'bias': source_info.get('bias', 'unknown'),
            'reason': f'Known reliable source: {source_info["type"]}'
        }
    
    if domain in UNRELIABLE_SOURCES:
        source_info = UNRELIABLE_SOURCES[domain]
        return {
            'credibility': 'unreliable',
            'score': source_info['score'],
            'issues': source_info.get('issues', []),
            'reason': 'Known problematic source'
        }
    
    return {
        'credibility': 'unknown',
        'score': 5,
        'reason': 'Source not in database - verify independently'
    }
