import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <nav className="nav">
        <div className="logo">
          <span className="logo-text">FakeNewsGuard</span>
        </div>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#about">About</a>
          <a href="#api">API</a>
          <a href="#resources">Resources</a>
          <a href="#contact">Contact</a>
        </div>
        <div className="auth-buttons">
          <button className="login-btn">Log in</button>
          <button className="signup-btn">Sign up</button>
        </div>
      </nav>
    </header>
  );
};

export default Header;
