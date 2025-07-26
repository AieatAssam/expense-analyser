import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  Skeleton,
  VStack,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from '@chakra-ui/react';
import { FiMoreVertical, FiDownload, FiRefreshCw } from 'react-icons/fi';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  isLoading?: boolean;
  onRefresh?: () => void;
  onExport?: () => void;
  height?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  children,
  isLoading = false,
  onRefresh,
  onExport,
  height = '400px',
}) => {
  if (isLoading) {
    return (
      <Card height={height}>
        <CardHeader>
          <VStack align="start" spacing={1}>
            <Skeleton height="24px" width="60%" />
            {subtitle && <Skeleton height="16px" width="40%" />}
          </VStack>
        </CardHeader>
        <CardBody pt={0}>
          <Skeleton height="300px" borderRadius="md" />
        </CardBody>
      </Card>
    );
  }

  return (
    <Card height={height}>
      <CardHeader pb={2}>
        <HStack justify="space-between" align="start">
          <VStack align="start" spacing={1}>
            <Heading size="md" color="gray.700">
              {title}
            </Heading>
            {subtitle && (
              <Text fontSize="sm" color="gray.600">
                {subtitle}
              </Text>
            )}
          </VStack>
          {(onRefresh || onExport) && (
            <Menu>
              <MenuButton
                as={IconButton}
                icon={<FiMoreVertical />}
                variant="ghost"
                size="sm"
                aria-label="Chart options"
              />
              <MenuList>
                {onRefresh && (
                  <MenuItem icon={<FiRefreshCw />} onClick={onRefresh}>
                    Refresh
                  </MenuItem>
                )}
                {onExport && (
                  <MenuItem icon={<FiDownload />} onClick={onExport}>
                    Export
                  </MenuItem>
                )}
              </MenuList>
            </Menu>
          )}
        </HStack>
      </CardHeader>
      <CardBody pt={0} display="flex" flexDirection="column">
        <Box flex="1" minH="0">
          {children}
        </Box>
      </CardBody>
    </Card>
  );
};