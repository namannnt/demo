# models/text_analyzer.py
"""
Simple text analyzer for testing
"""

class TextAnalyzer:
    def __init__(self):
        self.emotional_words = ['shocking', 'unbelievable', 'breaking', 'exclusive']
    
    def analyze_text(self, text, source_score=5):
        """Simple text analysis"""
        text_lower = text.lower()
        red_flags = 0
        issues = []
        
        # Check for emotional language
        emotional_count = sum(1 for word in self.emotional_words if word in text_lower)
        if emotional_count > 0:
            red_flags += emotional_count
            issues.append(f"Emotional language detected ({emotional_count} words)")
        
        # Check for excessive caps
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.2:
            red_flags += 1
            issues.append("Excessive capitalization")
        
        # Calculate score
        credibility_score = max(1, source_score - red_flags)
        
        if credibility_score >= 7:
            level = "Likely Reliable"
        elif credibility_score >= 4:
            level = "Questionable"
        else:
            level = "Likely Unreliable"
        
        return {
            'credibility_score': credibility_score,
            'credibility_level': level,
            'red_flags_count': red_flags,
            'issues_found': issues,
            'text_stats': {
                'word_count': len(text.split()),
                'character_count': len(text)
            }
        }
