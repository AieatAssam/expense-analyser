import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,

  Card,
  Badge,
  Separator,
  Button,
  // Menu,
  // MenuButton,
  // MenuList,
  // MenuItem,
  IconButton,
} from '@chakra-ui/react';
import { FiUser, FiSettings, FiMoreVertical, FiLogOut } from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';
import LogoutButton from '../auth/LogoutButton';
import AccountSwitcher from './AccountSwitcher';

interface UserProfileProps {
  variant?: 'compact' | 'detailed';
  showAccountSwitcher?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({
  variant = 'detailed',
  showAccountSwitcher = true,
}) => {
  const { userProfile } = useAuth();
  const cardBg = 'white';
  const borderColor = 'gray.200';

  if (!userProfile) {
    return null;
  }

  if (variant === 'compact') {
    return (
      <HStack gap={3} p={3}>
        <Box
          w="8"
          h="8"
          borderRadius="full"
          bg="blue.500"
          display="flex"
          alignItems="center"
          justifyContent="center"
          color="white"
          fontSize="sm"
          fontWeight="bold"
        >
          {(userProfile.user.name || userProfile.user.email)?.charAt(0)?.toUpperCase()}
        </Box>
        <VStack gap={0} align="start" flex="1">
          <Text fontSize="sm" fontWeight="medium" lineClamp={1}>
            {userProfile.user.name || userProfile.user.email}
          </Text>
          <Text fontSize="xs" color="gray.500" lineClamp={1}>
            {userProfile.currentAccount.name}
          </Text>
        </VStack>
        {/* <Menu>
          <MenuButton
            as={IconButton}
            icon={<FiMoreVertical />}
            variant="ghost"
            size="sm"
            aria-label="User menu"
          />
          <MenuList>
            <MenuItem icon={<FiUser />}>Profile</MenuItem>
            <MenuItem icon={<FiSettings />}>Settings</MenuItem>
            <MenuItem icon={<FiLogOut />}>
              <LogoutButton variant="text" />
            </MenuItem>
          </MenuList>
        </Menu> */}
      </HStack>
    );
  }

  return (
    <Card.Root bg={cardBg} borderColor={borderColor}>
      <Card.Body>
        <VStack gap={4} align="stretch">
          {/* User Header */}
          <HStack gap={3}>
            <Box
              w="12"
              h="12"
              borderRadius="full"
              bg="blue.500"
              display="flex"
              alignItems="center"
              justifyContent="center"
              color="white"
              fontSize="lg"
              fontWeight="bold"
            >
              {(userProfile.user.name || userProfile.user.email)?.charAt(0)?.toUpperCase()}
            </Box>
            <VStack gap={1} align="start" flex="1">
              <Text fontWeight="bold" fontSize="md" lineClamp={1}>
                {userProfile.user.name || userProfile.user.email}
              </Text>
              <Text fontSize="sm" color="gray.600" lineClamp={1}>
                {userProfile.user.email}
              </Text>
              <HStack gap={2}>
                <Badge colorPalette="blue" size="sm">
                  {userProfile.currentAccount.name}
                </Badge>
                {userProfile.accounts.length > 1 && (
                  <Badge colorPalette="gray" size="sm">
                    {userProfile.accounts.length} accounts
                  </Badge>
                )}
              </HStack>
            </VStack>
            {/* <Menu>
              <MenuButton
                as={IconButton}
                icon={<FiMoreVertical />}
                variant="ghost"
                size="sm"
                aria-label="User menu"
              />
              <MenuList>
                <MenuItem icon={<FiUser />}>Profile Settings</MenuItem>
                <MenuItem icon={<FiSettings />}>Account Settings</MenuItem>
                <Divider />
                <MenuItem icon={<FiLogOut />} color="red.500">
                  <LogoutButton variant="text" />
                </MenuItem>
              </MenuList>
            </Menu> */}
          </HStack>

          {/* Account Switcher */}
          {showAccountSwitcher && userProfile.accounts.length > 1 && (
            <>
              {/* <Divider /> */}
              <AccountSwitcher variant="menu" size="sm" />
            </>
          )}

          {/* Quick Actions */}
          {/* <Divider /> */}
          <VStack gap={2}>
            <Button
              variant="outline"
              size="sm"
              w="full"
              gap={2}
            >
              Account Settings
            </Button>
            <LogoutButton />
          </VStack>
        </VStack>
      </Card.Body>
    </Card.Root>
  );
};

export default UserProfile;
