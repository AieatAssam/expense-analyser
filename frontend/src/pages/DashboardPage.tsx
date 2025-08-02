import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  AlertRoot,
  AlertIndicator,
  useBreakpointValue,
  Button,
} from '@chakra-ui/react';
import { FiDollarSign, FiFileText, FiTrendingUp, FiShoppingBag, FiDownload } from 'react-icons/fi';
import { format, subDays } from 'date-fns';

import { DashboardLayout, DashboardGrid, DashboardCard, StatCard, ChartCard } from '../components/dashboard';
// import { LineChart, PieChart, BarChart } from '../components/charts';
// import { FilterPanel } from '../components/filters';
// import { ExportModal } from '../components/export';
// import UserProfile from '../components/user/UserProfile';
import { analyticsService, AnalyticsSummary, CategorySummary, SpendingTrend } from '../services/analyticsService';
import { useAuth } from '../contexts/AuthContext';

interface FilterState {
  search?: string;
  startDate?: string;
  endDate?: string;
  minAmount?: number;
  maxAmount?: number;
  sortBy?: 'receipt_date' | 'total_amount' | 'store_name' | 'created_at';
  sortOrder?: 'asc' | 'desc';
}

const DashboardPage: React.FC = () => {
  const { isAuthenticated, userProfile } = useAuth();
  const toast = useToast(); // Re-enabled for Chakra UI v3
  const [isExportOpen, setIsExportOpen] = useState(false);
  const onExportOpen = () => setIsExportOpen(true);
  const onExportClose = () => setIsExportOpen(false);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [categoryData, setCategoryData] = useState<CategorySummary[]>([]);
  const [trendData, setTrendData] = useState<SpendingTrend[]>([]);
  const [filters, setFilters] = useState<FilterState>({
    sortBy: 'receipt_date',
    sortOrder: 'desc',
  });

  const isMobile = useBreakpointValue({ base: true, md: false });

  useEffect(() => {
    if (isAuthenticated && userProfile) {
      loadDashboardData();
    }
  }, [isAuthenticated, userProfile]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load summary data
      const summaryData = await analyticsService.getAnalyticsSummary();
      setSummary(summaryData);

      // Load category breakdown (last 30 days)
      const endDate = new Date();
      const startDate = subDays(endDate, 30);
      const categories = await analyticsService.getCategoryBreakdown({
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
      });
      setCategoryData(categories);

      // Load spending trends (last 30 days)
      const trends = await analyticsService.getSpendingTrends({
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
      }, 'day');
      setTrendData(trends);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load dashboard data. Please try again.');
      console.error('Error loading dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    // In a real implementation, you'd reload data based on filters
    // For now, just show a toast
    console.log('Filters updated:', newFilters);
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  // Prepare chart data
  const categoryChartData = {
    labels: categoryData.map(cat => cat.category_name || 'Uncategorized'),
    datasets: [{
      label: 'Spending by Category',
      data: categoryData.map(cat => cat.total_amount),
    }],
  };

  const trendChartData = {
    labels: trendData.map(trend => format(new Date(trend.date), 'MMM dd')),
    datasets: [{
      label: 'Daily Spending',
      data: trendData.map(trend => trend.amount),
    }],
  };

  const receiptCountChartData = {
    labels: trendData.map(trend => format(new Date(trend.date), 'MMM dd')),
    datasets: [{
      label: 'Receipt Count',
      data: trendData.map(trend => trend.receipt_count),
    }],
  };

  if (!isAuthenticated) {
    return (
      <DashboardLayout title="Please log in to view your dashboard">
        <AlertRoot status="warning">
          <AlertIndicator />
          You need to be logged in to access the dashboard.
        </AlertRoot>
      </DashboardLayout>
    );
  }

  if (error && !isLoading) {
    return (
      <DashboardLayout title="Dashboard Error">
        <AlertRoot status="error">
          <AlertIndicator />
          {error}
        </AlertRoot>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Analytics Dashboard" isLoading={isLoading}>
      <VStack gap={6} align="stretch">
        {/* User Profile Section */}
        {!isMobile && (
          <Box>
            {/* <UserProfile variant="compact" /> */}
          </Box>
        )}

        {/* Filters and Export */}
        <VStack gap={4} align="stretch">
          <HStack justify="space-between" align="start">
            <Box flex="1">
              {/* <FilterPanel
                filters={filters}
                onChange={handleFilterChange}
                onReset={() => setFilters({ sortBy: 'receipt_date', sortOrder: 'desc' })}
              /> */}
            </Box>
            <Button
              colorPalette="blue"
              variant="outline"
              onClick={onExportOpen}
              size="md"
              disabled={isLoading || !summary}
              gap={2}
            >
              <FiDownload />
              Export
            </Button>
          </HStack>
        </VStack>

        {/* Summary Stats */}
        <DashboardGrid>
          <DashboardCard colSpan={{ base: 1, md: 1, lg: 1, xl: 1 }}>
            <StatCard
              label="Total Receipts"
              value={summary?.total_receipts || 0}
              icon={FiFileText}
              isLoading={isLoading}
              colorScheme="blue"
            />
          </DashboardCard>
          
          <DashboardCard colSpan={{ base: 1, md: 1, lg: 1, xl: 1 }}>
            <StatCard
              label="Total Spending"
              value={`$${(summary?.total_amount || 0).toFixed(2)}`}
              icon={FiDollarSign}
              isLoading={isLoading}
              colorScheme="green"
            />
          </DashboardCard>
          
          <DashboardCard colSpan={{ base: 1, md: 1, lg: 1, xl: 1 }}>
            <StatCard
              label="Average Receipt"
              value={`$${(summary?.average_receipt_amount || 0).toFixed(2)}`}
              icon={FiTrendingUp}
              isLoading={isLoading}
              colorScheme="purple"
            />
          </DashboardCard>
          
          <DashboardCard colSpan={{ base: 1, md: 1, lg: 1, xl: 1 }}>
            <StatCard
              label="Top Category"
              value={categoryData[0]?.category_name || 'N/A'}
              helpText={categoryData[0] ? `$${categoryData[0].total_amount.toFixed(2)}` : undefined}
              icon={FiShoppingBag}
              isLoading={isLoading}
              colorScheme="orange"
            />
          </DashboardCard>
        </DashboardGrid>

        {/* Charts */}
        <DashboardGrid>
          {/* Spending Trend Chart */}
          <DashboardCard colSpan={{ base: 1, md: 2, lg: 2, xl: 2 }}>
            <ChartCard
              title="Spending Trends"
              subtitle="Daily spending over the last 30 days"
              onRefresh={handleRefresh}
              isLoading={isLoading}
            >
              {trendData.length > 0 ? (
                <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                  <Text color="gray.500">Chart Component (LineChart)</Text>
                </Box>
              ) : (
                <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                  <Text color="gray.500">No spending data available</Text>
                </Box>
              )}
            </ChartCard>
          </DashboardCard>

          {/* Category Breakdown */}
          <DashboardCard colSpan={{ base: 1, md: 2, lg: 1, xl: 2 }}>
            <ChartCard
              title="Category Breakdown"
              subtitle="Spending by category (last 30 days)"
              onRefresh={handleRefresh}
              isLoading={isLoading}
            >
              {categoryData.length > 0 ? (
                <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                  <Text color="gray.500">Chart Component (PieChart)</Text>
                </Box>
              ) : (
                <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                  <Text color="gray.500">No category data available</Text>
                </Box>
              )}
            </ChartCard>
          </DashboardCard>

          {/* Receipt Count Chart */}
          <DashboardCard colSpan={{ base: 1, md: 2, lg: 2, xl: 2 }}>
            <ChartCard
              title="Receipt Activity"
              subtitle="Number of receipts processed daily"
              onRefresh={handleRefresh}
              isLoading={isLoading}
            >
              {trendData.length > 0 ? (
                <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                  <Text color="gray.500">Chart Component (BarChart)</Text>
                </Box>
              ) : (
                <Box height="300px" display="flex" alignItems="center" justifyContent="center">
                  <Text color="gray.500">No receipt data available</Text>
                </Box>
              )}
            </ChartCard>
          </DashboardCard>
        </DashboardGrid>
      </VStack>

      {/* Export Modal */}
      {/* <ExportModal isOpen={isExportOpen} onClose={onExportClose} /> */}
    </DashboardLayout>
  );
};

export default DashboardPage;