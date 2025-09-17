# utils/fact_checker.py
"""
Google Fact Check API integration for claim verification
"""
import requests
import os
import logging

logger = logging.getLogger(__name__)

class FactCheckAPI:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_FACT_CHECK_API_KEY')
        self.base_url = 'https://factchecktools.googleapis.com/v1alpha1/claims:search'
        
    def check_claims_with_google(self, text):
        """Query Google Fact Check Tools API for claim verification"""
        if not self.google_api_key:
            return {'error': 'Google Fact Check API key not configured'}
            
        # Extract key phrases from text (simple approach)
        query = self._extract_key_claims(text)
        
        params = {
            'key': self.google_api_key,
            'query': query,
            'languageCode': 'en',
            'maxAgeDays': 365  # Only check claims from last year
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return self._process_fact_check_results(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fact check API request failed: {str(e)}")
            return {'error': f'API request failed: {str(e)}'}
    
    def _extract_key_claims(self, text):
        """Extract key claims from text for fact-checking"""
        # Simple approach: take first 200 chars, remove common words
        words_to_remove = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'is', 'are', 'was', 'were']
        
        # Get first 200 characters
        query = text[:200]
        
        # Remove common words to focus on important claims
        words = query.lower().split()
        filtered_words = [word for word in words if word not in words_to_remove and len(word) > 3]
        
        return ' '.join(filtered_words[:20])  # Max 20 important words
    
    def _process_fact_check_results(self, data):
        """Process and structure fact-check API results"""
        claims = data.get('claims', [])
        
        if not claims:
            return {'claims_found': 0, 'verification_status': 'no_claims_found'}
        
        processed_claims = []
        false_claims = 0
        mixed_claims = 0
        
        for claim in claims:
            claim_reviews = claim.get('claimReview', [])
            
            for review in claim_reviews:
                rating = review.get('textualRating', '').lower()
                
                # Categorize ratings
                if any(word in rating for word in ['false', 'incorrect', 'wrong', 'misleading']):
                    false_claims += 1
                elif any(word in rating for word in ['mixed', 'partly', 'some']):
                    mixed_claims += 1
                
                processed_claims.append({
                    'claim_text': claim.get('text', ''),
                    'rating': rating,
                    'reviewer': review.get('publisher', {}).get('name', 'Unknown'),
                    'url': review.get('url', '')
                })
        
        return {
            'claims_found': len(processed_claims),
            'false_claims': false_claims,
            'mixed_claims': mixed_claims,
            'claims': processed_claims[:5],  # Return max 5 claims
            'verification_status': 'claims_found'
        }
    
    def integrate_with_analysis(self, text_analysis_result, fact_check_data):
        """Integrate fact-check results with existing text analysis"""
        if 'error' in fact_check_data:
            # If fact-check failed, don't modify analysis
            text_analysis_result['fact_check_status'] = 'unavailable'
            return text_analysis_result
        
        claims_found = fact_check_data.get('claims_found', 0)
        false_claims = fact_check_data.get('false_claims', 0)
        mixed_claims = fact_check_data.get('mixed_claims', 0)
        
        # Adjust credibility score based on fact-check results
        if false_claims > 0:
            # Penalize heavily for false claims
            penalty = min(false_claims * 2, 5)  # Max penalty of 5 points
            text_analysis_result['credibility_score'] = max(1, text_analysis_result['credibility_score'] - penalty)
            text_analysis_result['issues_found'].append(f'{false_claims} claims fact-checked as FALSE or MISLEADING')
        
        if mixed_claims > 0:
            # Smaller penalty for mixed claims
            penalty = min(mixed_claims, 2)  # Max penalty of 2 points
            text_analysis_result['credibility_score'] = max(1, text_analysis_result['credibility_score'] - penalty)
            text_analysis_result['issues_found'].append(f'{mixed_claims} claims fact-checked as MIXED or PARTLY TRUE')
        
        # Add fact-check info to results
        text_analysis_result['fact_check'] = {
            'claims_found': claims_found,
            'false_claims': false_claims,
            'mixed_claims': mixed_claims,
            'sample_claims': fact_check_data.get('claims', [])[:3]  # Show max 3 examples
        }
        
        return text_analysis_result
