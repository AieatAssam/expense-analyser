import React from 'react';
import { Button } from '@chakra-ui/react';
import { useAuth } from '../../contexts/AuthContext';

const LogoutButton: React.FC = () => {
  const { logout } = useAuth();

  return (
    <Button
      colorScheme="red"
      variant="outline"
      onClick={logout}
    >
      Log Out
    </Button>
  );
};

export default LogoutButton;
