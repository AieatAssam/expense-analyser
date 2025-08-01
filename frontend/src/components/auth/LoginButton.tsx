import React from 'react';
import { Button } from '@chakra-ui/react';
import { useAuth } from '../../contexts/AuthContext';

const LoginButton: React.FC = () => {
  const { login, isLoading } = useAuth();

  return (
    <Button
      colorScheme="blue"
      onClick={login}
      disabled={isLoading}
    >
      {isLoading ? 'Loading...' : 'Log In'}
    </Button>
  );
};

export default LoginButton;
