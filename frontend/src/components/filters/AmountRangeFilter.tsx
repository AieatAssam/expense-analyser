import React from 'react';
import {
  Box,
  FieldRoot,
  FieldLabel,
  NumberInputRoot,
  NumberInputInput,
  HStack,
  Text,
  VStack,
  Button,
} from '@chakra-ui/react';

interface AmountRangeFilterProps {
  minAmount?: number;
  maxAmount?: number;
  onChange: (minAmount?: number, maxAmount?: number) => void;
  label?: string;
  currency?: string;
}

export const AmountRangeFilter: React.FC<AmountRangeFilterProps> = ({
  minAmount,
  maxAmount,
  onChange,
  label = 'Amount Range',
  currency = '$',
}) => {
  const handleMinChange = (valueString: string) => {
    const value = parseFloat(valueString);
    onChange(isNaN(value) ? undefined : value, maxAmount);
  };

  const handleMaxChange = (valueString: string) => {
    const value = parseFloat(valueString);
    onChange(minAmount, isNaN(value) ? undefined : value);
  };

  const setQuickRange = (min?: number, max?: number) => {
    onChange(min, max);
  };

  const clearRange = () => {
    onChange(undefined, undefined);
  };

  const quickRanges = [
    { label: 'Under $10', min: undefined, max: 10 },
    { label: '$10 - $50', min: 10, max: 50 },
    { label: '$50 - $100', min: 50, max: 100 },
    { label: 'Over $100', min: 100, max: undefined },
  ];

  return (
    <Box>
      <FieldLabel fontSize="sm" fontWeight="medium" mb={3}>
        {label}
      </FieldLabel>
      <VStack gap={4} align="stretch">
        {/* Amount inputs */}
        <HStack gap={3}>
          <FieldRoot flex="1">
            <FieldLabel fontSize="xs" color="gray.600">Min Amount</FieldLabel>
            <NumberInputRoot
              value={minAmount?.toString() || ''}
              onValueChange={(details) => handleMinChange(details.value)}
              min={0}
              formatOptions={{ minimumFractionDigits: 2 }}
              size="sm"
            >
              <NumberInputInput placeholder="0.00" />
            </NumberInputRoot>
          </FieldRoot>
          <FieldRoot flex="1">
            <FieldLabel fontSize="xs" color="gray.600">Max Amount</FieldLabel>
            <NumberInputRoot
              value={maxAmount?.toString() || ''}
              onValueChange={(details) => handleMaxChange(details.value)}
              min={0}
              formatOptions={{ minimumFractionDigits: 2 }}
              size="sm"
            >
              <NumberInputInput placeholder="No limit" />
            </NumberInputRoot>
          </FieldRoot>
        </HStack>

        {/* Quick range buttons */}
        <Box>
          <Text fontSize="xs" color="gray.600" mb={2}>Quick select:</Text>
          <VStack gap={1}>
            {quickRanges.map((range) => (
              <Button
                key={range.label}
                size="xs"
                variant="outline"
                w="full"
                onClick={() => setQuickRange(range.min, range.max)}
                colorScheme="blue"
              >
                {range.label}
              </Button>
            ))}
            <Button
              size="xs"
              variant="outline"
              w="full"
              onClick={clearRange}
              colorScheme="gray"
            >
              Clear
            </Button>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};