import React, { useState } from 'react';
import './MainContent.css';

const MainContent = ({ onAnalysis, isLoading }) => {
  const [inputText, setInputText] = useState('');
  const [inputMethod, setInputMethod] = useState('text'); 

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim()) {
      onAnalysis(inputText);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setInputText(event.target.result);
        setInputMethod('text');
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="main-content">
      <div className="content-header">
        <div className="badge">
          <span className="badge-icon">🔍</span>
          <span>FAKE NEWS DETECTION</span>
        </div>
        
        <h1 className="main-title">
          Detect fake news with advanced AI analysis, 
          get instant credibility insights
        </h1>
        
        <p className="main-description">
          Use our advanced AI model to analyze news articles and text content for 
          credibility indicators, bias detection, and fact-verification across multiple 
          sources with detailed confidence scoring and explanations.
        </p>
      </div>

      <div className="input-card">
        <div className="input-tabs">
          <button 
            className={`tab ${inputMethod === 'text' ? 'active' : ''}`}
            onClick={() => setInputMethod('text')}
          >
            <span className="tab-icon">📝</span>
            Text Input
          </button>
          <button 
            className={`tab ${inputMethod === 'file' ? 'active' : ''}`}
            onClick={() => setInputMethod('file')}
          >
            <span className="tab-icon">📄</span>
            File Upload
          </button>
        </div>

        {inputMethod === 'text' ? (
          <form onSubmit={handleSubmit} className="text-input-form">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste your news article or text content here for analysis..."
              className="text-input"
              rows={8}
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="analyze-button"
              disabled={!inputText.trim() || isLoading}
            >
              {isLoading ? 'ANALYZING...' : 'ANALYZE TEXT'}
            </button>
          </form>
        ) : (
          <div className="file-upload-area">
            <p className="upload-instruction">
              Choose a text file or drag and drop it here
            </p>
            <input
              type="file"
              accept=".txt,.doc,.docx"
              onChange={handleFileUpload}
              className="file-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="upload-button">
              UPLOAD FILE
            </label>
          </div>
        )}
      </div>
    </div>
  );
};

export default MainContent;
