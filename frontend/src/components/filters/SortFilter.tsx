import React from 'react';
import {
  Box,
  FieldRoot,
  FieldLabel,


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
      <FieldLabel fontSize="sm" fontWeight="medium" mb={3}>
        {label}
      </FieldLabel>
      <HStack gap={2}>
        <FieldRoot flex="1">
          <select
            value={sortBy}
            onChange={handleSortByChange}
            style={{
              backgroundColor: 'white',
              border: '1px solid #E2E8F0',
              borderRadius: '6px',
              padding: '6px',
              width: '100%',
              fontSize: '14px'
            }}
          >
            {fields.map((field) => (
              <option key={field.value} value={field.value}>
                {field.label}
              </option>
            ))}
          </select>
        </FieldRoot>
        <IconButton
          aria-label={`Sort ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
          size="sm"
          variant="outline"
          onClick={toggleSortOrder}
          colorPalette="blue"
        >
          {sortOrder === 'asc' ? '↑' : '↓'}
        </IconButton>
      </HStack>
    </Box>
  );
};