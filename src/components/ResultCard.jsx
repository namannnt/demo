import React from 'react';
import './ResultCard.css';

const ResultCard = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <div className="result-card loading">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h3>Analyzing content...</h3>
          <p>Please wait while we process your text</p>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const isReal = result.verdict.includes('Real');
  
  return (
    <div className="result-card">
      <div className="result-header">
        <h3>Analysis Result</h3>
        <div className={`verdict ${isReal ? 'real' : 'fake'}`}>
          <span className="verdict-icon">
            {isReal ? '✓' : '⚠️'}
          </span>
          <span className="verdict-text">{result.verdict}</span>
        </div>
      </div>

      <div className="confidence-bar">
        <div className="confidence-label">
          Confidence Score: {result.confidence}%
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${result.confidence}%` }}
          ></div>
        </div>
      </div>

      <div className="analysis-details">
        <h4>Analysis Summary</h4>
        <p>{result.analysis}</p>
        
        <h4>Key Factors</h4>
        <ul className="factors-list">
          {result.keyFactors.map((factor, index) => (
            <li key={index}>{factor}</li>
          ))}
        </ul>
      </div>

      <div className="result-actions">
        <button className="secondary-button">View Detailed Report</button>
        <button className="primary-button">Share Results</button>
      </div>
    </div>
  );
};

export default ResultCard;
