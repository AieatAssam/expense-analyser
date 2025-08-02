import React from 'react';
import {
  Card,
  Heading,
  Text,
  Skeleton,
  VStack,
  HStack,
  IconButton,
  Menu,
  Box,
  Icon,
  Portal,
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
      <Card.Root height={height}>
        <Card.Header>
          <VStack align="start" gap={1}>
            <Skeleton height="24px" width="60%" />
            {subtitle && <Skeleton height="16px" width="40%" />}
          </VStack>
        </Card.Header>
        <Card.Body pt={0}>
          <Skeleton height="300px" borderRadius="md" />
        </Card.Body>
      </Card.Root>
    );
  }

  return (
    <Card.Root height={height}>
      <Card.Header pb={2}>
        <HStack justify="space-between" align="start">
          <VStack align="start" gap={1}>
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
            <Menu.Root>
              <Menu.Trigger asChild>
                <IconButton
                  variant="ghost"
                  size="sm"
                  aria-label="Chart options"
                >
                  ⋮
                </IconButton>
              </Menu.Trigger>
              <Portal>
                <Menu.Positioner>
                  <Menu.Content>
                    {onRefresh && (
                      <Menu.Item value="refresh" onClick={onRefresh}>
                        🔄 Refresh
                      </Menu.Item>
                    )}
                    {onExport && (
                      <Menu.Item value="export" onClick={onExport}>
                        📥 Export
                      </Menu.Item>
                    )}
                  </Menu.Content>
                </Menu.Positioner>
              </Portal>
            </Menu.Root>
          )}
        </HStack>
      </Card.Header>
      <Card.Body pt={0} display="flex" flexDirection="column">
        <Box flex="1" minH="0">
          {children}
        </Box>
      </Card.Body>
    </Card.Root>
  );
};