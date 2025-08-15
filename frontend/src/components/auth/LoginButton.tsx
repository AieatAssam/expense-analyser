import React from 'react';
import { Button } from '@chakra-ui/react';
import { useAuth } from '../../contexts/AuthContext';

const LoginButton: React.FC = () => {
  const { login, isLoading, isAuthenticated } = useAuth();

  if (isAuthenticated) return null;

  return (
    <Button
      colorPalette="blue"
      onClick={() => login()}
      size="lg"
      disabled={isLoading}
    >
      {isLoading ? 'Loading...' : 'Log In'}
    </Button>
  );
};

export default LoginButton;
