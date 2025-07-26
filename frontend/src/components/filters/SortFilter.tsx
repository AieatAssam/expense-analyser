import React from 'react';
import {
  Box,
  FormControl,
  FormLabel,
  Select,
  HStack,
  IconButton,
} from '@chakra-ui/react';
import { FiArrowUp, FiArrowDown } from 'react-icons/fi';

type SortField = 'receipt_date' | 'total_amount' | 'store_name' | 'created_at';
type SortOrder = 'asc' | 'desc';

interface SortFilterProps {
  sortBy?: SortField;
  sortOrder?: SortOrder;
  onChange: (sortBy?: SortField, sortOrder?: SortOrder) => void;
  label?: string;
  fields?: { value: SortField; label: string }[];
}

const defaultFields = [
  { value: 'receipt_date' as SortField, label: 'Receipt Date' },
  { value: 'total_amount' as SortField, label: 'Amount' },
  { value: 'store_name' as SortField, label: 'Store Name' },
  { value: 'created_at' as SortField, label: 'Upload Date' },
];

export const SortFilter: React.FC<SortFilterProps> = ({
  sortBy = 'receipt_date',
  sortOrder = 'desc',
  onChange,
  label = 'Sort by',
  fields = defaultFields,
}) => {
  const handleSortByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSortBy = e.target.value as SortField;
    onChange(newSortBy, sortOrder);
  };

  const toggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    onChange(sortBy, newOrder);
  };

  return (
    <Box>
      <FormLabel fontSize="sm" fontWeight="medium" mb={3}>
        {label}
      </FormLabel>
      <HStack spacing={2}>
        <FormControl flex="1">
          <Select
            value={sortBy}
            onChange={handleSortByChange}
            size="sm"
            bg="white"
            borderColor="gray.200"
          >
            {fields.map((field) => (
              <option key={field.value} value={field.value}>
                {field.label}
              </option>
            ))}
          </Select>
        </FormControl>
        <IconButton
          aria-label={`Sort ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
          icon={sortOrder === 'asc' ? <FiArrowUp /> : <FiArrowDown />}
          size="sm"
          variant="outline"
          onClick={toggleSortOrder}
          colorScheme="blue"
        />
      </HStack>
    </Box>
  );
};