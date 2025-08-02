import React, { useState } from 'react';
import {
  Box,
  Text,
  Select,
  MenuRoot,
  MenuTrigger,
  MenuContent,
  MenuItem,
  Button,
  HStack,
  VStack,
  Badge,
  Avatar,
  Spinner,
} from '@chakra-ui/react';
import { FiChevronDown, FiCheck, FiUser } from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';

interface AccountSwitcherProps {
  variant?: 'select' | 'menu';
  size?: 'sm' | 'md' | 'lg';
}

const AccountSwitcher: React.FC<AccountSwitcherProps> = ({
  variant = 'menu',
  size = 'md',
}) => {
  const { userProfile, switchAccount } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  if (!userProfile || userProfile.accounts.length <= 1) {
    return null;
  }

  const handleAccountSwitch = async (accountId: string) => {
    if (accountId === userProfile.currentAccount.id) return;
    
    setIsLoading(true);
    try {
      await switchAccount(accountId);
      const account = userProfile.accounts.find(acc => acc.id === accountId);
      console.log('Account switched to:', account?.name);
    } catch (error) {
      console.error('Failed to switch account:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (variant === 'select') {
    return (
      <Box>
        <Text fontSize="sm" mb={2} fontWeight="medium" color="gray.700">
          Current Account
        </Text>
        <Select.Root
          value={[userProfile.currentAccount.id]}
          onValueChange={(details) => handleAccountSwitch(details.value[0])}
        >
          <Select.Trigger bg="white" borderColor="gray.200">
            <Select.ValueText placeholder="Select account" />
          </Select.Trigger>
          <Select.Content>
            {userProfile.accounts.map((account) => (
              <Select.Item key={account.id} item={account.id}>
                <Select.ItemText>{account.name}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Content>
        </Select.Root>
      </Box>
    );
  }

  return (
    <Box>
      <Text fontSize="sm" mb={2} fontWeight="medium" color="gray.700">
        Current Account
      </Text>
      <MenuRoot>
        <MenuTrigger asChild>
          <Button
          variant="outline"
          size={size}
          w="full"
          justifyContent="space-between"
          bg="white"
          borderColor="gray.200"
          disabled={isLoading}
        >
          <HStack gap={2}>
            <Box
              w="6"
              h="6"
              borderRadius="full"
              bg="blue.500"
              display="flex"
              alignItems="center"
              justifyContent="center"
              color="white"
              fontSize="xs"
              fontWeight="bold"
            >
              {userProfile.currentAccount.name?.charAt(0)?.toUpperCase()}
            </Box>
            <VStack gap={0} align="start">
              <Text fontSize="sm" fontWeight="medium">
                {userProfile.currentAccount.name}
              </Text>
              {userProfile.accounts.length > 1 && (
                <Text fontSize="xs" color="gray.500">
                  {userProfile.accounts.length} accounts
                </Text>
              )}
            </VStack>
          </HStack>
          </Button>
        </MenuTrigger>
        <MenuContent>
          {userProfile.accounts.map((account) => (
            <MenuItem
              key={account.id}
              value={account.id}
              onClick={() => handleAccountSwitch(account.id)}
            >
              <HStack gap={2} mr={2}>
                {account.id === userProfile.currentAccount.id ? (
                  <Text color="green.500" fontSize="sm">✓</Text>
                ) : (
                  <Box
                    w="6"
                    h="6"
                    borderRadius="full"
                    bg="gray.400"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    color="white"
                    fontSize="xs"
                    fontWeight="bold"
                  >
                    {account.name?.charAt(0)?.toUpperCase()}
                  </Box>
                )}
              </HStack>
              <HStack justify="space-between" w="full">
                <VStack gap={0} align="start">
                  <Text fontSize="sm" fontWeight="medium">
                    {account.name}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {account.id}
                  </Text>
                </VStack>
                {account.id === userProfile.currentAccount.id && (
                  <Badge colorPalette="green" size="sm">
                    Current
                  </Badge>
                )}
              </HStack>
            </MenuItem>
          ))}
        </MenuContent>
      </MenuRoot>
    </Box>
  );
};

export default AccountSwitcher;
