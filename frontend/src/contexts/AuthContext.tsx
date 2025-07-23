import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { setAuthToken, clearAuthToken } from '../services/api';
import { userService } from '../services/userService';
import { UserProfile } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  userProfile: UserProfile | null;
  login: () => void;
  logout: () => void;
  switchAccount: (accountId: string) => Promise<boolean>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  userProfile: null,
  login: () => {},
  logout: () => {},
  switchAccount: async () => false,
  error: null,
});

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const { isAuthenticated, isLoading: auth0Loading, loginWithRedirect, logout: auth0Logout, getAccessTokenSilently, user } = useAuth0();
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  // Handle auth token and user profile
  useEffect(() => {
    const fetchUserData = async () => {
      if (isAuthenticated && user) {
        try {
          // Get access token from Auth0
          const token = await getAccessTokenSilently();
          
          // Store token for API requests
          setAuthToken(token);
          
          // Fetch user profile with accounts
          const profile = await userService.getUserProfile();
          setUserProfile(profile);
          setError(null);
        } catch (err) {
          console.error('Error fetching user data:', err);
          setError('Failed to load user profile');
        } finally {
          setIsLoading(false);
        }
      } else if (!auth0Loading) {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, [isAuthenticated, user, auth0Loading, getAccessTokenSilently]);

  const login = () => {
    loginWithRedirect();
  };

  const logout = () => {
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });
    clearAuthToken();
    setUserProfile(null);
  };

  const switchAccount = async (accountId: string): Promise<boolean> => {
    try {
      await userService.switchAccount(accountId);
      
      // Update user profile with new current account
      const profile = await userService.getUserProfile();
      setUserProfile(profile);
      return true;
    } catch (err) {
      console.error('Error switching account:', err);
      setError('Failed to switch account');
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading: isLoading || auth0Loading,
        userProfile,
        login,
        logout,
        switchAccount,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

export default AuthContext;
