# utils/web_scraper.py
"""
Simple web scraper for testing
"""
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_page_content(self, url, timeout=10):
        """Simple webpage content fetcher"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic content
            title = soup.find('title')
            title_text = title.get_text().strip() if title else 'No title'
            
            # Get all paragraph text
            paragraphs = soup.find_all('p')
            main_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return {
                'title': title_text,
                'main_content': main_content[:5000],
                'has_main_content': bool(main_content),
                'word_count': len(main_content.split())
            }
        except Exception as e:
            return {'error': f'Failed to fetch webpage: {str(e)}'}
