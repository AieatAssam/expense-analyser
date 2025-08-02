import React, { useState, useEffect } from 'react';
import {
  InputGroup,
  InputElement,
  Input,
  IconButton,
  FieldRoot,
  FieldLabel,
  Text,
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
    <FieldRoot>
      <Text fontSize="sm" fontWeight="medium" mb={2}>{label}</Text>
      <Input
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        size="sm"
        bg="white"
        borderColor="gray.200"
        style={{
          paddingLeft: '2.5rem',
          backgroundImage: 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%23cbd5e0\'%3e%3cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z\'%3e%3c/path%3e%3c/svg%3e")',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: '0.75rem center',
          backgroundSize: '1rem 1rem'
        }}
        _hover={{ borderColor: 'gray.300' }}
        _focus={{ borderColor: 'blue.500', boxShadow: '0 0 0 1px #3182ce' }}
      />
      {localValue && (
        <IconButton
          aria-label="Clear search"
          size="sm"
          variant="ghost"
          onClick={handleClear}
          marginLeft="0.5rem"
        >
          ×
        </IconButton>
      )}
    </FieldRoot>
  );
};