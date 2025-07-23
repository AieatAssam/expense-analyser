import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { useAuth0 } from '@auth0/auth0-react';

// Mock dependencies
jest.mock('@auth0/auth0-react', () => {
  return {
    useAuth0: jest.fn(),
    // Add other Auth0 exports that might be needed
    Auth0Provider: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="auth0-provider">{children}</div>
    ),
  };
});

// Mock userService module
jest.mock('../services/userService', () => {
  return {
    userService: {
      getUserProfile: jest.fn(),
      switchAccount: jest.fn(),
    },
  };
});

// Test component that uses the auth context
const TestComponent = () => {
  const { isAuthenticated, userProfile, login, logout } = useAuth();
  return (
    <div>
      {isAuthenticated ? (
        <div>
          <span>Authenticated</span>
          {userProfile && (
            <div data-testid="user-email">{userProfile.user.email}</div>
          )}
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={login}>Login</button>
      )}
    </div>
  );
};

describe('AuthContext', () => {
  const mockLoginWithRedirect = jest.fn();
  const mockLogout = jest.fn();
  const mockGetAccessTokenSilently = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Set up default mock implementation
    (useAuth0 as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      loginWithRedirect: mockLoginWithRedirect,
      logout: mockLogout,
      getAccessTokenSilently: mockGetAccessTokenSilently,
      user: null,
    });
  });
  
  test('provides authentication state when not authenticated', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.queryByText('Authenticated')).not.toBeInTheDocument();
  });
  
  test('provides authentication state when authenticated', async () => {
    const mockUser = {
      email: 'test@example.com',
      name: 'Test User',
    };
    
    const mockProfile = {
      user: {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
      },
      accounts: [
        {
          id: 'acc1',
          name: 'Account 1',
        },
      ],
      currentAccount: {
        id: 'acc1',
        name: 'Account 1',
      },
    };
    
    // Mock authenticated state
    (useAuth0 as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      loginWithRedirect: mockLoginWithRedirect,
      logout: mockLogout,
      getAccessTokenSilently: mockGetAccessTokenSilently,
      user: mockUser,
    });
    
    // Mock successful token retrieval
    mockGetAccessTokenSilently.mockResolvedValueOnce('test-token');
    
    // Mock user profile retrieval
    const { userService } = require('../services/userService');
    userService.getUserProfile.mockResolvedValue(mockProfile);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Wait for async operations to complete
    await waitFor(() => {
      expect(screen.getByText('Authenticated')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Wait for the user profile to be loaded and rendered
    await waitFor(() => {
      const emailElement = screen.getByTestId('user-email');
      expect(emailElement).toHaveTextContent('test@example.com');
    }, { timeout: 5000 });
    
    // Check if token was retrieved and user profile was fetched
    expect(mockGetAccessTokenSilently).toHaveBeenCalled();
    expect(userService.getUserProfile).toHaveBeenCalled();
  });
  
  test('handles login action', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Click login button
    screen.getByText('Login').click();
    
    // Check if Auth0 login was called
    expect(mockLoginWithRedirect).toHaveBeenCalled();
  });
  
  test('handles logout action', async () => {
    // Mock authenticated state
    (useAuth0 as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      loginWithRedirect: mockLoginWithRedirect,
      logout: mockLogout,
      getAccessTokenSilently: mockGetAccessTokenSilently,
      user: { email: 'test@example.com' },
    });
    
    // Mock successful token and profile retrieval
    mockGetAccessTokenSilently.mockResolvedValueOnce('test-token');
    
    // Mock user profile retrieval
    const { userService } = require('../services/userService');
    userService.getUserProfile.mockResolvedValue({
      user: { id: '123', email: 'test@example.com' },
      accounts: [{ id: 'acc1', name: 'Account 1' }],
      currentAccount: { id: 'acc1', name: 'Account 1' },
    });
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Wait for authenticated state
    await waitFor(() => {
      expect(screen.getByText('Authenticated')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Click logout button
    screen.getByText('Logout').click();
    
    // Wait for Auth0 logout to be called
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledWith(
        expect.objectContaining({
          logoutParams: expect.objectContaining({
            returnTo: window.location.origin
          })
        })
      );
    });
  });
});
