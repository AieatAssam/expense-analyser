import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Text,
  Switch,
  FormControl,
  FormLabel,
  Input,
  Alert,
  AlertIcon,
  Progress,
  useToast,
  Divider,
  Badge,
  Box,
} from '@chakra-ui/react';
import { FiDownload, FiFileText, FiCalendar } from 'react-icons/fi';
import { format } from 'date-fns';

import { exportService, ExportQuery, ExportInfo } from '../../services/exportService';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [includeLineItems, setIncludeLineItems] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [exportInfo, setExportInfo] = useState<ExportInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toast = useToast();

  const handlePreview = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const query: ExportQuery = {
        include_line_items: includeLineItems,
      };
      
      if (startDate) query.start_date = startDate;
      if (endDate) query.end_date = endDate;
      
      const info = await exportService.getExportInfo(query);
      setExportInfo(info);
      
    } catch (error) {
      console.error('Error getting export info:', error);
      setError('Failed to get export information. Please try again.');
      toast({
        title: 'Export Preview Failed',
        description: 'Unable to preview export. Please check your date range and try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    setDownloadProgress(0);
    setError(null);
    
    try {
      const query: ExportQuery = {
        include_line_items: includeLineItems,
      };
      
      if (startDate) query.start_date = startDate;
      if (endDate) query.end_date = endDate;
      
      await exportService.downloadExcelWithProgress(query, (progress) => {
        setDownloadProgress(progress);
      });
      
      toast({
        title: 'Export Complete',
        description: 'Your expense data has been downloaded successfully.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      onClose();
      
    } catch (error) {
      console.error('Error downloading export:', error);
      setError('Failed to download export. Please try again.');
      toast({
        title: 'Download Failed',
        description: 'Unable to download export file. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsDownloading(false);
      setDownloadProgress(0);
    }
  };

  const handleClose = () => {
    if (!isDownloading) {
      setStartDate('');
      setEndDate('');
      setIncludeLineItems(true);
      setExportInfo(null);
      setError(null);
      setDownloadProgress(0);
      onClose();
    }
  };

  const isDateRangeValid = !startDate || !endDate || startDate <= endDate;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <HStack>
            <FiDownload />
            <Text>Export Expense Data</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton isDisabled={isDownloading} />
        
        <ModalBody>
          <VStack spacing={6} align="stretch">
            {/* Date Range Selection */}
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={3} color="gray.700">
                Date Range (Optional)
              </Text>
              <HStack spacing={3}>
                <FormControl>
                  <FormLabel fontSize="xs" color="gray.600">From</FormLabel>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    size="sm"
                    isDisabled={isDownloading}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="xs" color="gray.600">To</FormLabel>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    size="sm"
                    isDisabled={isDownloading}
                  />
                </FormControl>
              </HStack>
              {!isDateRangeValid && (
                <Text fontSize="xs" color="red.500" mt={1}>
                  End date must be after start date
                </Text>
              )}
            </Box>

            {/* Export Options */}
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={3} color="gray.700">
                Export Options
              </Text>
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="include-line-items" mb="0" fontSize="sm">
                  Include detailed line items
                </FormLabel>
                <Switch
                  id="include-line-items"
                  isChecked={includeLineItems}
                  onChange={(e) => setIncludeLineItems(e.target.checked)}
                  isDisabled={isDownloading}
                />
              </FormControl>
              <Text fontSize="xs" color="gray.500" mt={1}>
                Creates a separate sheet with individual purchase items
              </Text>
            </Box>

            {/* Export Preview */}
            {exportInfo && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={3} color="gray.700">
                  Export Preview
                </Text>
                <VStack spacing={2} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="sm">Records to export:</Text>
                    <Badge colorScheme="blue">{exportInfo.records_count} receipts</Badge>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Date range:</Text>
                    <Text fontSize="sm" color="gray.600">{exportInfo.date_range}</Text>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Filename:</Text>
                    <Text fontSize="sm" color="gray.600" fontFamily="mono">
                      {exportInfo.filename}
                    </Text>
                  </HStack>
                </VStack>
              </Box>
            )}

            {/* Download Progress */}
            {isDownloading && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={2}>
                  Downloading... {downloadProgress}%
                </Text>
                <Progress value={downloadProgress} colorScheme="blue" size="sm" />
              </Box>
            )}

            {/* Error Display */}
            {error && (
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                <Text fontSize="sm">{error}</Text>
              </Alert>
            )}

            {/* File Format Info */}
            <Box bg="gray.50" p={3} borderRadius="md">
              <HStack mb={2}>
                <FiFileText />
                <Text fontSize="sm" fontWeight="medium">Excel Format (.xlsx)</Text>
              </HStack>
              <Text fontSize="xs" color="gray.600">
                Your export will include:
              </Text>
              <VStack align="start" spacing={1} mt={1}>
                <Text fontSize="xs" color="gray.600">• Summary sheet with export statistics</Text>
                <Text fontSize="xs" color="gray.600">• Receipts overview with totals and status</Text>
                {includeLineItems && (
                  <Text fontSize="xs" color="gray.600">• Detailed line items with categories</Text>
                )}
              </VStack>
            </Box>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack spacing={3}>
            <Button
              variant="outline"
              onClick={handleClose}
              isDisabled={isDownloading}
              size="sm"
            >
              Cancel
            </Button>
            <Button
              onClick={handlePreview}
              isLoading={isLoading}
              loadingText="Checking..."
              size="sm"
              isDisabled={!isDateRangeValid || isDownloading}
            >
              Preview
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleDownload}
              isLoading={isDownloading}
              loadingText={`Downloading... ${downloadProgress}%`}
              leftIcon={<FiDownload />}
              size="sm"
              isDisabled={!isDateRangeValid || !exportInfo}
            >
              Download
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};