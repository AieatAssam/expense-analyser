import React, { useState, useEffect } from 'react';
import {
  InputGroup,
  InputLeftElement,
  Input,
  InputRightElement,
  IconButton,
  FormControl,
  FormLabel,
} from '@chakra-ui/react';
import { FiSearch, FiX } from 'react-icons/fi';

interface SearchFilterProps {
  value?: string;
  onChange: (value?: string) => void;
  placeholder?: string;
  label?: string;
  debounceMs?: number;
}

export const SearchFilter: React.FC<SearchFilterProps> = ({
  value = '',
  onChange,
  placeholder = 'Search receipts...',
  label = 'Search',
  debounceMs = 300,
}) => {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue || undefined);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [localValue, onChange, debounceMs]);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleClear = () => {
    setLocalValue('');
  };

  return (
    <FormControl>
      <FormLabel fontSize="sm" fontWeight="medium">
        {label}
      </FormLabel>
      <InputGroup>
        <InputLeftElement pointerEvents="none">
          <FiSearch color="gray.300" />
        </InputLeftElement>
        <Input
          value={localValue}
          onChange={(e) => setLocalValue(e.target.value)}
          placeholder={placeholder}
          size="md"
          bg="white"
          borderColor="gray.200"
          _hover={{ borderColor: 'gray.300' }}
          _focus={{ borderColor: 'blue.500', boxShadow: '0 0 0 1px #3182ce' }}
        />
        {localValue && (
          <InputRightElement>
            <IconButton
              aria-label="Clear search"
              icon={<FiX />}
              size="sm"
              variant="ghost"
              onClick={handleClear}
            />
          </InputRightElement>
        )}
      </InputGroup>
    </FormControl>
  );
};