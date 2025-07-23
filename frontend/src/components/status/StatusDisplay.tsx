import React, { useEffect, useState } from 'react';
import { Box, Text, Flex, Icon } from '@chakra-ui/react';
import { FiCheckCircle, FiAlertCircle, FiClock, FiLoader } from 'react-icons/fi';
import { Receipt, ReceiptProcessingStatus } from '../../types';
import { useProcessingStatus } from '../../contexts/ProcessingStatusContext';
import receiptService from '../../services/receiptService';

interface StatusDisplayProps {
  receipt: Receipt;
  onStatusUpdate?: (updatedReceipt: Receipt) => void;
}

const StatusDisplay: React.FC<StatusDisplayProps> = ({ receipt, onStatusUpdate }) => {
  const { receiptStatuses, statusMessages } = useProcessingStatus();
  const [localStatus, setLocalStatus] = useState<ReceiptProcessingStatus>(receipt.status);
  const [localMessage, setLocalMessage] = useState<string | undefined>(undefined);

  // Update status from WebSocket or poll for status
  useEffect(() => {
    // If we have a status from WebSocket, use it
    if (receiptStatuses[receipt.id]) {
      const newStatus = receiptStatuses[receipt.id];
      setLocalStatus(newStatus);
      
      if (statusMessages[receipt.id]) {
        setLocalMessage(statusMessages[receipt.id]);
      }

      if (onStatusUpdate) {
        onStatusUpdate({
          ...receipt,
          status: newStatus,
        });
      }
    } else {
      // Otherwise, poll the status
      const fetchStatus = async () => {
        try {
          const statusData = await receiptService.getReceiptStatus(receipt.id);
          const newStatus = statusData.status as ReceiptProcessingStatus;
          
          setLocalStatus(newStatus);
          if (statusData.message) {
            setLocalMessage(statusData.message);
          }

          if (onStatusUpdate) {
            onStatusUpdate({
              ...receipt,
              status: newStatus,
            });
          }

          // Stop polling if we're in a terminal state
          return newStatus === ReceiptProcessingStatus.COMPLETED || 
                 newStatus === ReceiptProcessingStatus.ERROR;
        } catch (error) {
          console.error('Error fetching receipt status:', error);
          return false;
        }
      };

      // Only poll if not in a terminal state
      if (
        localStatus !== ReceiptProcessingStatus.COMPLETED && 
        localStatus !== ReceiptProcessingStatus.ERROR
      ) {
        const intervalId = setInterval(async () => {
          const shouldStop = await fetchStatus();
          if (shouldStop) {
            clearInterval(intervalId);
          }
        }, 5000);

        return () => {
          clearInterval(intervalId);
        };
      }
    }
  }, [receipt, receiptStatuses, statusMessages, localStatus, onStatusUpdate]);

  // Render different status indicators based on status
  const renderStatusIndicator = () => {
    switch (localStatus) {
      case ReceiptProcessingStatus.UPLOADING:
        return (
          <Flex align="center" color="blue.500">
            <Icon as={FiLoader} mr={2} />
            <Text>Uploading...</Text>
          </Flex>
        );
      case ReceiptProcessingStatus.PENDING:
        return (
          <Flex align="center" color="orange.500">
            <Icon as={FiClock} mr={2} />
            <Text>Pending processing...</Text>
          </Flex>
        );
      case ReceiptProcessingStatus.PROCESSING:
        return (
          <Flex align="center" color="blue.500">
            <Icon as={FiLoader} mr={2} className="spinning" />
            <Text>Processing receipt...</Text>
          </Flex>
        );
      case ReceiptProcessingStatus.COMPLETED:
        return (
          <Flex align="center" color="green.500">
            <Icon as={FiCheckCircle} mr={2} />
            <Text>Processing completed</Text>
          </Flex>
        );
      case ReceiptProcessingStatus.ERROR:
        return (
          <Flex align="center" color="red.500">
            <Icon as={FiAlertCircle} mr={2} />
            <Text>Processing failed</Text>
          </Flex>
        );
      default:
        return null;
    }
  };

  // Determine progress value based on status
  const getProgressValue = () => {
    switch (localStatus) {
      case ReceiptProcessingStatus.UPLOADING:
        return 20;
      case ReceiptProcessingStatus.PENDING:
        return 40;
      case ReceiptProcessingStatus.PROCESSING:
        return 60;
      case ReceiptProcessingStatus.COMPLETED:
        return 100;
      case ReceiptProcessingStatus.ERROR:
        return 100;
      default:
        return 0;
    }
  };

  // Determine progress color based on status
  const getProgressColor = () => {
    if (localStatus === ReceiptProcessingStatus.ERROR) {
      return "red";
    } else if (localStatus === ReceiptProcessingStatus.COMPLETED) {
      return "green";
    }
    return "blue";
  };

  return (
    <Box 
      borderWidth={1} 
      borderRadius="md" 
      p={4} 
      borderColor="gray.200"
      bg={localStatus === ReceiptProcessingStatus.ERROR ? "red.50" : "white"}
    >
      <Flex justify="space-between" mb={2}>
        <Text fontWeight="medium">{receipt.fileName}</Text>
        <Text fontSize="sm" color="gray.600">
          {new Date(receipt.uploadDate).toLocaleString()}
        </Text>
      </Flex>

      <Box
        w="100%"
        h="8px"
        bg="gray.100"
        borderRadius="full"
        overflow="hidden"
        mb={3}
      >
        <Box
          w={`${getProgressValue()}%`}
          h="100%"
          bg={`${getProgressColor()}.500`}
          transition="width 0.3s ease-in-out"
        />
      </Box>

      <Flex justify="space-between" align="center">
        {renderStatusIndicator()}
      </Flex>

      {localMessage && (
        <Text fontSize="sm" mt={2} color={localStatus === ReceiptProcessingStatus.ERROR ? "red.500" : "gray.600"}>
          {localMessage}
        </Text>
      )}

      <style dangerouslySetInnerHTML={{
        __html: `
          .spinning {
            animation: spin 2s linear infinite;
          }
          @keyframes spin {
            from {transform: rotate(0deg);}
            to {transform: rotate(360deg);}
          }
        `
      }} />
    </Box>
  );
};

export default StatusDisplay;
