import React from 'react';
import { Button } from '@chakra-ui/react';
import { useAuth } from '../../contexts/AuthContext';

const LogoutButton: React.FC = () => {
  const { logout } = useAuth();

  return (
    <Button
      onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
      colorPalette="red"
      variant="outline"
    >
      Log Out
    </Button>
  );
};

export default LogoutButton;
