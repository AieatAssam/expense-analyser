import React from 'react';
import { Grid, GridItem, useBreakpointValue } from '@chakra-ui/react';

interface DashboardGridProps {
  children: React.ReactNode;
}

interface DashboardCardProps {
  children: React.ReactNode;
  colSpan?: {
    base?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  rowSpan?: {
    base?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({ children }) => {
  const gridColumns = useBreakpointValue({ 
    base: 'repeat(1, 1fr)', 
    md: 'repeat(2, 1fr)', 
    lg: 'repeat(3, 1fr)', 
    xl: 'repeat(4, 1fr)' 
  });

  return (
    <Grid templateColumns={gridColumns} gap={6} w="full">
      {children}
    </Grid>
  );
};

export const DashboardCard: React.FC<DashboardCardProps> = ({ 
  children, 
  colSpan = { base: 1 },
  rowSpan = { base: 1 }
}) => {
  return (
    <GridItem colSpan={colSpan} rowSpan={rowSpan}>
      {children}
    </GridItem>
  );
};