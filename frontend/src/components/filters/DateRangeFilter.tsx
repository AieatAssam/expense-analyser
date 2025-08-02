import React from 'react';
import {
  Box,
  FieldRoot,
  FieldLabel,
  Input,
  HStack,
  VStack,
  Button,
  Text,
  useBreakpointValue,
} from '@chakra-ui/react';
import { format, subDays, subWeeks, subMonths, startOfDay } from 'date-fns';

interface DateRangeFilterProps {
  startDate?: string;
  endDate?: string;
  onDateChange: (startDate?: string, endDate?: string) => void;
  label?: string;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  startDate,
  endDate,
  onDateChange,
  label = 'Date Range',
}) => {
  const isMobile = useBreakpointValue({ base: true, md: false });

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onDateChange(e.target.value || undefined, endDate);
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onDateChange(startDate, e.target.value || undefined);
  };

  const setQuickRange = (days: number) => {
    const end = new Date();
    const start = subDays(end, days);
    onDateChange(
      format(start, 'yyyy-MM-dd'),
      format(end, 'yyyy-MM-dd')
    );
  };

  const setWeekRange = (weeks: number) => {
    const end = new Date();
    const start = subWeeks(end, weeks);
    onDateChange(
      format(start, 'yyyy-MM-dd'),
      format(end, 'yyyy-MM-dd')
    );
  };

  const setMonthRange = (months: number) => {
    const end = new Date();
    const start = subMonths(end, months);
    onDateChange(
      format(start, 'yyyy-MM-dd'),
      format(end, 'yyyy-MM-dd')
    );
  };

  const clearRange = () => {
    onDateChange(undefined, undefined);
  };

  const quickOptions = [
    { label: 'Last 7 days', action: () => setQuickRange(7) },
    { label: 'Last 30 days', action: () => setQuickRange(30) },
    { label: 'Last 3 months', action: () => setMonthRange(3) },
    { label: 'Last 6 months', action: () => setMonthRange(6) },
    { label: 'Clear', action: clearRange },
  ];

  return (
    <Box>
      <FieldLabel fontSize="sm" fontWeight="medium" mb={3}>
        {label}
      </FieldLabel>
      <VStack gap={4} align="stretch">
        {/* Date inputs */}
        <HStack gap={3} direction={isMobile ? 'column' : 'row'}>
          <FieldRoot flex="1">
            <FieldLabel fontSize="xs" color="gray.600">From</FieldLabel>
            <Input
              type="date"
              value={startDate || ''}
              onChange={handleStartDateChange}
              size="sm"
            />
          </FieldRoot>
          <FieldRoot flex="1">
            <FieldLabel fontSize="xs" color="gray.600">To</FieldLabel>
            <Input
              type="date"
              value={endDate || ''}
              onChange={handleEndDateChange}
              size="sm"
            />
          </FieldRoot>
        </HStack>

        {/* Quick range buttons */}
        <Box>
          <Text fontSize="xs" color="gray.600" mb={2}>Quick select:</Text>
          <VStack gap={2}>
            {isMobile ? (
              <VStack gap={1} w="full">
                {quickOptions.map((option) => (
                  <Button
                    key={option.label}
                    size="xs"
                    variant="outline"
                    w="full"
                    onClick={option.action}
                    colorPalette={option.label === 'Clear' ? 'gray' : 'blue'}
                  >
                    {option.label}
                  </Button>
                ))}
              </VStack>
            ) : (
              <HStack gap={1} wrap="wrap">
                {quickOptions.map((option) => (
                  <Button
                    key={option.label}
                    size="xs"
                    variant="outline"
                    onClick={option.action}
                    colorPalette={option.label === 'Clear' ? 'gray' : 'blue'}
                  >
                    {option.label}
                  </Button>
                ))}
              </HStack>
            )}
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};