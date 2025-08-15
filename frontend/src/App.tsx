import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { ChakraProvider } from '@chakra-ui/react';
import { system } from './theme';
import { AuthProvider } from './contexts/AuthContext';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import LoginButton from './components/auth/LoginButton';

import './App.css';

// Auth0 configuration - using Vite environment variables
const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN || '';
const auth0ClientId = import.meta.env.VITE_AUTH0_CLIENT_ID || '';
const auth0Audience = import.meta.env.VITE_AUTH0_AUDIENCE || '';

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
          redirect_uri: `${window.location.origin}/callback`,
          audience: auth0Audience,
        }}
        // Persist the session across reloads and in browsers that block 3rd-party cookies
        // Uses Rotating Refresh Tokens and stores the cache in localStorage
        cacheLocation="localstorage"
        useRefreshTokens={true}
        useRefreshTokensFallback={true}
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
                <Route path="/callback" element={<AuthCallback />} />
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

// Minimal callback gate to allow the Auth0 SDK to finish handling the code/state
const AuthCallback: React.FC = () => {
  const { isLoading } = useAuth0();

  // While Auth0 processes the callback, keep a simple loading state.
  if (isLoading) {
    return <div style={{ padding: 24 }}>Signing you in…</div>;
  }

  // Once done, send the user to the dashboard (App's onRedirectCallback already cleaned the URL)
  return <Navigate to="/dashboard" replace />;
};

export default App;
