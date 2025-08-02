import React from 'react';
import {
  Box,
  Stat,
  Card,
  Skeleton,
  Icon,
  HStack,
  VStack,
} from '@chakra-ui/react';
import { IconType } from 'react-icons';

interface StatCardProps {
  label: string;
  value: string | number;
  helpText?: string;
  trend?: 'increase' | 'decrease';
  trendValue?: string;
  icon?: IconType;
  isLoading?: boolean;
  colorPalette?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  helpText,
  trend,
  trendValue,
  icon,
  isLoading = false,
  colorPalette = 'blue',
}) => {
  if (isLoading) {
    return (
      <Card.Root>
        <Card.Body>
          <VStack align="start" gap={3}>
            <Skeleton height="20px" width="60%" />
            <Skeleton height="32px" width="80%" />
            <Skeleton height="16px" width="40%" />
          </VStack>
        </Card.Body>
      </Card.Root>
    );
  }

  return (
    <Card.Root>
      <Card.Body>
        <Stat.Root>
          <HStack justify="space-between" align="start">
            <VStack align="start" gap={1} flex="1">
              <Stat.Label fontSize="sm" color="gray.600" fontWeight="medium">
                {label}
              </Stat.Label>
              <Stat.ValueText fontSize="2xl" fontWeight="bold" color="gray.900">
                {value}
              </Stat.ValueText>
              {(helpText || (trend && trendValue)) && (
                <Stat.HelpText mb={0} fontSize="sm">
                  {trend && trendValue && (
                    <>
                      {trend === 'increase' ? <Stat.UpIndicator /> : <Stat.DownIndicator />}
                      {trendValue}
                      {helpText && ' '}
                    </>
                  )}
                  {helpText}
                </Stat.HelpText>
              )}
            </VStack>
            {icon && (
              <Box p={2} bg={`${colorPalette}.50`} borderRadius="md">
                📊
              </Box>
            )}
          </HStack>
        </Stat.Root>
      </Card.Body>
    </Card.Root>
  );
};