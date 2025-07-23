import React from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { useAuth } from '../../contexts/AuthContext';
import LogoutButton from '../auth/LogoutButton';
import AccountSwitcher from './AccountSwitcher';

const UserProfile: React.FC = () => {
  const { userProfile } = useAuth();

  if (!userProfile) {
    return null;
  }

  return (
    <Box mb={4}>
      <Flex alignItems="center" mb={3}>
        <div style={{ 
          width: '32px', 
          height: '32px', 
          borderRadius: '50%', 
          backgroundColor: '#4299E1',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          marginRight: '8px',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          {(userProfile.user.name || userProfile.user.email).charAt(0).toUpperCase()}
        </div>
        <Box>
          <Text fontWeight="bold" fontSize="sm">
            {userProfile.user.name || userProfile.user.email}
          </Text>
          <Text fontSize="xs" color="gray.600">
            {userProfile.currentAccount.name}
          </Text>
        </Box>
        <Box ml="auto">
          <LogoutButton />
        </Box>
      </Flex>
      <AccountSwitcher />
    </Box>
  );
};

export default UserProfile;
