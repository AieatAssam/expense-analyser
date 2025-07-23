const React = require('react');

// Mock user data
const mockUser = {
  email: 'test@example.com',
  email_verified: true,
  sub: 'auth0|123456789',
  name: 'Test User',
  nickname: 'testuser',
  picture: 'https://example.com/avatar.png',
};

// Mock Auth0 context value with default authenticated state
const mockContextValue = {
  isAuthenticated: true,
  user: mockUser,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('mock-access-token'),
  getIdTokenClaims: jest.fn().mockResolvedValue({
    __raw: 'mock-id-token',
    exp: Math.floor(Date.now() / 1000) + 86400,
  }),
};

// Mock the useAuth0 hook
const useAuth0 = jest.fn(() => mockContextValue);

// Mock Auth0Provider component
const Auth0Provider = ({ children }) => {
  return React.createElement('div', { 'data-testid': 'auth0-provider' }, children);
};

// Mock withAuthenticationRequired HOC
const withAuthenticationRequired = (Component, options) => {
  const WithAuthenticationRequired = (props) => {
    return React.createElement(Component, props);
  };
  WithAuthenticationRequired.displayName = `withAuthenticationRequired(${Component.displayName || 'Component'})`;
  return WithAuthenticationRequired;
};

// Export all the mock functions
module.exports = {
  useAuth0,
  Auth0Provider,
  withAuthenticationRequired,
  // Helper to manipulate the mock state
  mockContextValue,
};
