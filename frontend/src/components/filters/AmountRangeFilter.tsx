import React from 'react';
import {
  Box,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
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
      <FormLabel fontSize="sm" fontWeight="medium" mb={3}>
        {label}
      </FormLabel>
      <VStack spacing={4} align="stretch">
        {/* Amount inputs */}
        <HStack spacing={3}>
          <FormControl flex="1">
            <FormLabel fontSize="xs" color="gray.600">Min Amount</FormLabel>
            <NumberInput
              value={minAmount || ''}
              onChange={handleMinChange}
              min={0}
              precision={2}
              size="sm"
            >
              <NumberInputField placeholder="0.00" />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>
          <FormControl flex="1">
            <FormLabel fontSize="xs" color="gray.600">Max Amount</FormLabel>
            <NumberInput
              value={maxAmount || ''}
              onChange={handleMaxChange}
              min={0}
              precision={2}
              size="sm"
            >
              <NumberInputField placeholder="No limit" />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>
        </HStack>

        {/* Quick range buttons */}
        <Box>
          <Text fontSize="xs" color="gray.600" mb={2}>Quick select:</Text>
          <VStack spacing={1}>
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