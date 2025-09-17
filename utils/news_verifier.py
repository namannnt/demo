# utils/news_verifier.py
"""
NewsAPI integration for cross-referencing claims with recent news
"""
import requests
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsVerifier:
    def __init__(self):
        self.api_key = os.getenv('NEWSAPI_API_KEY')
        self.base_url = 'https://newsapi.org/v2/everything'
        
    def verify_news_claims(self, text, max_articles=5):
        """Cross-reference text claims with recent news articles"""
        if not self.api_key:
            return {'error': 'NewsAPI key not configured'}
        
        # Extract keywords for news search
        keywords = self._extract_keywords(text)
        
        params = {
            'q': keywords,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': max_articles,
            'apiKey': self.api_key,
            'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')  # Last 30 days
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return self._process_news_results(data, keywords)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI request failed: {str(e)}")
            return {'error': f'News verification failed: {str(e)}'}
    
    def _extract_keywords(self, text):
        """Extract relevant keywords from text for news search"""
        # Simple keyword extraction
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = text.lower().split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 4]
        
        # Take most important keywords (first few content words)
        return ' '.join(keywords[:5])
    
    def _process_news_results(self, data, search_keywords):
        """Process news API results and analyze for verification"""
        articles = data.get('articles', [])
        
        if not articles:
            return {
                'articles_found': 0,
                'verification_status': 'no_related_news',
                'search_keywords': search_keywords
            }
        
        processed_articles = []
        reliable_sources = {'reuters.com', 'apnews.com', 'bbc.com', 'npr.org'}
        reliable_count = 0
        
        for article in articles:
            source_name = article.get('source', {}).get('name', '')
            source_url = article.get('url', '')
            
            # Check if source is reliable
            is_reliable = any(reliable in source_url.lower() for reliable in reliable_sources)
            if is_reliable:
                reliable_count += 1
            
            processed_articles.append({
                'title': article.get('title', ''),
                'source': source_name,
                'url': source_url,
                'published_at': article.get('publishedAt', ''),
                'description': article.get('description', '')[:200],  # First 200 chars
                'is_reliable_source': is_reliable
            })
        
        return {
            'articles_found': len(processed_articles),
            'reliable_sources_count': reliable_count,
            'articles': processed_articles,
            'search_keywords': search_keywords,
            'verification_status': 'related_news_found'
        }
    
    def integrate_with_analysis(self, text_analysis_result, news_data):
        """Integrate news verification with text analysis"""
        if 'error' in news_data:
            text_analysis_result['news_verification'] = 'unavailable'
            return text_analysis_result
        
        articles_found = news_data.get('articles_found', 0)
        reliable_sources = news_data.get('reliable_sources_count', 0)
        
        # Boost credibility if reliable sources found
        if reliable_sources >= 2:
            boost = min(reliable_sources, 3)  # Max boost of 3 points
            text_analysis_result['credibility_score'] = min(10, text_analysis_result['credibility_score'] + boost)
            text_analysis_result['issues_found'].append(f'Content corroborated by {reliable_sources} reliable news sources')
        
        # Add news verification info
        text_analysis_result['news_verification'] = {
            'articles_found': articles_found,
            'reliable_sources_count': reliable_sources,
            'sample_articles': news_data.get('articles', [])[:3]  # Show max 3 examples
        }
        
        return text_analysis_result
