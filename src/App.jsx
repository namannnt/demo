import React, { useState } from 'react';
import Header from './components/Header';
import MainContent from './components/MainContent';
import ResultCard from './components/ResultCard';
import './App.css';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalysis = async (text) => {
    setIsLoading(true);
    setAnalysisResult(null);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock result
    const result = {
      verdict: Math.random() > 0.5 ? 'Likely Real' : 'Likely Fake',
      confidence: Math.round(75 + Math.random() * 20),
      analysis: 'This analysis is based on language patterns, fact-checking databases, and source credibility indicators.',
      keyFactors: [
        'Source credibility: Medium',
        'Emotional language: Low',
        'Fact verification: Partial match',
        'Bias indicators: Minimal'
      ]
    };
    
    setAnalysisResult(result);
    setIsLoading(false);
  };

  return (
    <div className="App">
      <Header />
      <main className="main-container">
        <MainContent onAnalysis={handleAnalysis} isLoading={isLoading} />
        {(analysisResult || isLoading) && (
          <ResultCard result={analysisResult} isLoading={isLoading} />
        )}
      </main>
    </div>
  );
}

export default App;
