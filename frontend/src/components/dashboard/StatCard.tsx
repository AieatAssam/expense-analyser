import React from 'react';
import {
  Box,
  StatRoot,
  StatLabel,
  StatValueText,
  StatHelpText,
  StatUpIndicator,
  StatDownIndicator,
  CardRoot,
  CardBody,
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
  colorScheme?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  helpText,
  trend,
  trendValue,
  icon,
  isLoading = false,
  colorScheme = 'blue',
}) => {
  if (isLoading) {
    return (
      <CardRoot>
        <CardBody>
          <VStack align="start" gap={3}>
            <Skeleton height="20px" width="60%" />
            <Skeleton height="32px" width="80%" />
            <Skeleton height="16px" width="40%" />
          </VStack>
        </CardBody>
      </CardRoot>
    );
  }

  return (
    <CardRoot>
      <CardBody>
        <StatRoot>
          <HStack justify="space-between" align="start">
            <VStack align="start" gap={1} flex="1">
              <StatLabel fontSize="sm" color="gray.600" fontWeight="medium">
                {label}
              </StatLabel>
              <StatValueText fontSize="2xl" fontWeight="bold" color="gray.900">
                {value}
              </StatValueText>
              {(helpText || (trend && trendValue)) && (
                <StatHelpText mb={0} fontSize="sm">
                  {trend && trendValue && (
                    <>
                      {trend === 'increase' ? <StatUpIndicator /> : <StatDownIndicator />}
                      {trendValue}
                      {helpText && ' '}
                    </>
                  )}
                  {helpText}
                </StatHelpText>
              )}
            </VStack>
            {icon && (
              <Box p={2} bg={`${colorScheme}.50`} borderRadius="md">
                📊
              </Box>
            )}
          </HStack>
        </StatRoot>
      </CardBody>
    </CardRoot>
  );
};