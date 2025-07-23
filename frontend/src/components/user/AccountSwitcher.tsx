import React from 'react';
import { Box, Text } from '@chakra-ui/react';
import { useAuth } from '../../contexts/AuthContext';

const AccountSwitcher: React.FC = () => {
  const { userProfile, switchAccount } = useAuth();

  if (!userProfile || userProfile.accounts.length <= 1) {
    return null;
  }

  const handleAccountChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const accountId = e.target.value;
    await switchAccount(accountId);
  };

  return (
    <Box mb={4}>
      <Text fontSize="sm" mb={1}>Current Account:</Text>
      <select 
        value={userProfile.currentAccount.id} 
        onChange={handleAccountChange}
        style={{ padding: '4px 8px', fontSize: '14px', width: '100%', borderRadius: '4px', borderColor: '#e2e8f0' }}
      >
        {userProfile.accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.name}
          </option>
        ))}
      </select>
    </Box>
  );
};

export default AccountSwitcher;
