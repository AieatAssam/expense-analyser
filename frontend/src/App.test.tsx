import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock Auth0 directly in the test file
jest.mock('@auth0/auth0-react', () => ({
  Auth0Provider: ({ children }: { children: React.ReactNode }) => <div data-testid="auth0-provider">{children}</div>,
  useAuth0: () => ({
    isAuthenticated: false,
    user: null,
    isLoading: false,
    loginWithRedirect: jest.fn(),
    logout: jest.fn(),
    getAccessTokenSilently: jest.fn().mockResolvedValue('test-token'),
  }),
}));

test('renders login button when unauthenticated', () => {
  render(<App />);
  // We should see a login button
  const loginButton = screen.getByTestId('mock-Button');
  expect(loginButton).toBeInTheDocument();
  
  // The app title should be present
  expect(screen.getByText('Expense Analyser')).toBeInTheDocument();
});
