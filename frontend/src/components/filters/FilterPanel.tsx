import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Button,
  Text,
  Separator,
  Card,
  CardBody,
  Badge,
} from '@chakra-ui/react';
import { FiFilter, FiRefreshCw } from 'react-icons/fi';
import { DateRangeFilter } from './DateRangeFilter';
import { SearchFilter } from './SearchFilter';
import { AmountRangeFilter } from './AmountRangeFilter';
import { SortFilter } from './SortFilter';

interface FilterState {
  search?: string;
  startDate?: string;
  endDate?: string;
  minAmount?: number;
  maxAmount?: number;
  sortBy?: 'receipt_date' | 'total_amount' | 'store_name' | 'created_at';
  sortOrder?: 'asc' | 'desc';
}

interface FilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  onReset?: () => void;
  showAdvanced?: boolean;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onChange,
  onReset,
  showAdvanced = true,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  const updateFilters = (updates: Partial<FilterState>) => {
    onChange({ ...filters, ...updates });
  };

  const handleReset = () => {
    const resetFilters: FilterState = {
      sortBy: 'receipt_date',
      sortOrder: 'desc',
    };
    onChange(resetFilters);
    if (onReset) onReset();
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.search) count++;
    if (filters.startDate || filters.endDate) count++;
    if (filters.minAmount !== undefined || filters.maxAmount !== undefined) count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <Card.Root>
        <CardBody>
          <VStack gap={4} align="stretch">
            {/* Header */}
            <HStack justify="space-between" align="center">
              <HStack>
                <Button
                  // eslint-disable-next-line react/style-prop-object
                  style={{
                    gap: 2,
                  }}

                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(!isOpen)}
                >
                  Filters
                </Button>
              </HStack>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={activeFilterCount === 0}
              >
                Reset
              </Button>
            </HStack>

            {isOpen && (
              <VStack gap={6} align="stretch">
                {/* Search */}
                <SearchFilter
                  value={filters.search}
                  onChange={(search) => updateFilters({ search })}
                  placeholder="Search store names..."
                />

                {showAdvanced && (
                  <>
                    <Separator />
                    {/* Date Range */}
                    <DateRangeFilter
                      startDate={filters.startDate}
                      endDate={filters.endDate}
                      onDateChange={(startDate, endDate) =>
                        updateFilters({ startDate, endDate })
                      }
                    />

                    <Separator />

                    {/* Amount Range */}
                    <AmountRangeFilter
                      minAmount={filters.minAmount}
                      maxAmount={filters.maxAmount}
                      onChange={(minAmount, maxAmount) =>
                        updateFilters({ minAmount, maxAmount })
                      }
                    />

                    <Separator />

                    {/* Sort */}
                    <SortFilter
                      sortBy={filters.sortBy}
                      sortOrder={filters.sortOrder}
                      onChange={(sortBy, sortOrder) =>
                        updateFilters({ sortBy, sortOrder })
                      }
                    />
                  </>
                )}
              </VStack>
            )}
          </VStack>
        </CardBody>
    </Card.Root>
  );
};