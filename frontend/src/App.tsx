import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Auth0Provider } from '@auth0/auth0-react';
import { ChakraProvider } from '@chakra-ui/react';
import { system } from './theme';
import { AuthProvider } from './contexts/AuthContext';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import LoginButton from './components/auth/LoginButton';

import './App.css';

// Auth0 configuration
const auth0Domain = process.env.REACT_APP_AUTH0_DOMAIN || '';
const auth0ClientId = process.env.REACT_APP_AUTH0_CLIENT_ID || '';
const auth0Audience = process.env.REACT_APP_AUTH0_AUDIENCE || '';

const App: React.FC = () => {
  const onRedirectCallback = (appState: any) => {
    window.history.replaceState(
      {},
      document.title,
      appState?.returnTo || window.location.pathname
    );
  };

  return (
    <ChakraProvider value={system}>
      <Auth0Provider
        domain={auth0Domain}
        clientId={auth0ClientId}
        authorizationParams={{
          redirect_uri: window.location.origin,
          audience: auth0Audience,
        }}
        onRedirectCallback={onRedirectCallback}
      >
        <AuthProvider>
          <Router>
            <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
              <header style={{ 
                backgroundColor: 'white', 
                borderBottom: '1px solid #e2e8f0', 
                padding: '16px 0', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
              }}>
                <div style={{ 
                  maxWidth: '1024px', 
                  margin: '0 auto', 
                  padding: '0 16px', 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center' 
                }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold' }}>Expense Analyser</div>
                  <LoginButton />
                </div>
              </header>

              <Routes>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          </Router>
        </AuthProvider>
      </Auth0Provider>
    </ChakraProvider>
  );
};

export default App;
