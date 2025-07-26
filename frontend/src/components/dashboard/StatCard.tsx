import React from 'react';
import {
  Box,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Card,
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
      <Card>
        <CardBody>
          <VStack align="start" spacing={3}>
            <Skeleton height="20px" width="60%" />
            <Skeleton height="32px" width="80%" />
            <Skeleton height="16px" width="40%" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardBody>
        <Stat>
          <HStack justify="space-between" align="start">
            <VStack align="start" spacing={1} flex="1">
              <StatLabel fontSize="sm" color="gray.600" fontWeight="medium">
                {label}
              </StatLabel>
              <StatNumber fontSize="2xl" fontWeight="bold" color="gray.900">
                {value}
              </StatNumber>
              {(helpText || (trend && trendValue)) && (
                <StatHelpText mb={0} fontSize="sm">
                  {trend && trendValue && (
                    <>
                      <StatArrow type={trend} />
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
                <Icon as={icon} boxSize={6} color={`${colorScheme}.500`} />
              </Box>
            )}
          </HStack>
        </Stat>
      </CardBody>
    </Card>
  );
};