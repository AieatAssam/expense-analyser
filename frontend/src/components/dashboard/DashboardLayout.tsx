import React from 'react';
import {
  Box,
  Container,
  Grid,
  GridItem,
  Heading,
  VStack,
  useBreakpointValue,
  Skeleton,
} from '@chakra-ui/react';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  isLoading?: boolean;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  title = 'Analytics Dashboard',
  isLoading = false,
}) => {
  const gridColumns = useBreakpointValue({ base: 1, md: 2, lg: 3, xl: 4 });
  const containerPadding = useBreakpointValue({ base: 4, md: 6, lg: 8 });

  if (isLoading) {
    return (
      <Container maxW="full" py={containerPadding} px={containerPadding}>
        <VStack spacing={6} align="stretch">
          <Skeleton height="40px" width="300px" />
          <Grid templateColumns={`repeat(${gridColumns}, 1fr)`} gap={6}>
            {Array.from({ length: 6 }).map((_, index) => (
              <GridItem key={index} colSpan={index === 0 ? { base: 1, lg: 2 } : 1}>
                <Skeleton height="300px" borderRadius="md" />
              </GridItem>
            ))}
          </Grid>
        </VStack>
      </Container>
    );
  }

  return (
    <Container maxW="full" py={containerPadding} px={containerPadding}>
      <VStack spacing={6} align="stretch">
        <Heading size="lg" color="gray.700">
          {title}
        </Heading>
        <Box>
          {children}
        </Box>
      </VStack>
    </Container>
  );
};