import React, { useState } from 'react';
import {
  Box,
  Text,
  Select,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
  HStack,
  VStack,
  Badge,
  Avatar,
  useToast,
  Spinner,
} from '@chakra-ui/react';
import { FiChevronDown, FiCheck, FiBuilding } from 'react-icons/fi';
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
  const toast = useToast();

  if (!userProfile || userProfile.accounts.length <= 1) {
    return null;
  }

  const handleAccountSwitch = async (accountId: string) => {
    if (accountId === userProfile.currentAccount.id) return;
    
    setIsLoading(true);
    try {
      await switchAccount(accountId);
      const account = userProfile.accounts.find(acc => acc.id === accountId);
      toast({
        title: 'Account switched',
        description: `Now viewing ${account?.name}`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Failed to switch account',
        description: 'Please try again',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
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
        <Select
          value={userProfile.currentAccount.id}
          onChange={(e) => handleAccountSwitch(e.target.value)}
          size={size}
          bg="white"
          borderColor="gray.200"
          isDisabled={isLoading}
        >
          {userProfile.accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </Select>
      </Box>
    );
  }

  return (
    <Box>
      <Text fontSize="sm" mb={2} fontWeight="medium" color="gray.700">
        Current Account
      </Text>
      <Menu>
        <MenuButton
          as={Button}
          rightIcon={isLoading ? <Spinner size="sm" /> : <FiChevronDown />}
          variant="outline"
          size={size}
          w="full"
          justifyContent="space-between"
          bg="white"
          borderColor="gray.200"
          isDisabled={isLoading}
        >
          <HStack spacing={2}>
            <Avatar
              size="xs"
              name={userProfile.currentAccount.name}
              icon={<FiBuilding />}
              bg="blue.500"
            />
            <VStack spacing={0} align="start">
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
        </MenuButton>
        <MenuList>
          {userProfile.accounts.map((account) => (
            <MenuItem
              key={account.id}
              onClick={() => handleAccountSwitch(account.id)}
              icon={
                account.id === userProfile.currentAccount.id ? (
                  <FiCheck color="green" />
                ) : (
                  <Avatar
                    size="xs"
                    name={account.name}
                    icon={<FiBuilding />}
                    bg="gray.400"
                  />
                )
              }
            >
              <HStack justify="space-between" w="full">
                <VStack spacing={0} align="start">
                  <Text fontSize="sm" fontWeight="medium">
                    {account.name}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {account.id}
                  </Text>
                </VStack>
                {account.id === userProfile.currentAccount.id && (
                  <Badge colorScheme="green" size="sm">
                    Current
                  </Badge>
                )}
              </HStack>
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </Box>
  );
};

export default AccountSwitcher;
