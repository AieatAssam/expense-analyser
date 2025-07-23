import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import websocketService from '../services/websocketService';
import { useAuth } from './AuthContext';
import { ReceiptProcessingStatus } from '../types';

interface ReceiptStatusUpdate {
  receiptId: string;
  status: ReceiptProcessingStatus;
  message?: string;
}

interface ProcessingStatusContextType {
  receiptStatuses: Record<string, ReceiptProcessingStatus>;
  statusMessages: Record<string, string>;
  isConnected: boolean;
}

const ProcessingStatusContext = createContext<ProcessingStatusContextType>({
  receiptStatuses: {},
  statusMessages: {},
  isConnected: false,
});

interface ProcessingStatusProviderProps {
  children: ReactNode;
}

export const ProcessingStatusProvider = ({ children }: ProcessingStatusProviderProps) => {
  const { isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [receiptStatuses, setReceiptStatuses] = useState<Record<string, ReceiptProcessingStatus>>({});
  const [statusMessages, setStatusMessages] = useState<Record<string, string>>({});

  // Connect to WebSocket when authenticated
  useEffect(() => {
    const connectWebSocket = async () => {
      if (isAuthenticated) {
        const token = localStorage.getItem('auth_token') || '';
        const connected = await websocketService.connect(token);
        setIsConnected(connected);
      } else {
        websocketService.disconnect();
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      websocketService.disconnect();
    };
  }, [isAuthenticated]);

  // Subscribe to status updates
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = websocketService.subscribe<ReceiptStatusUpdate>('receipt_status', (data) => {
      if (data && data.receiptId) {
        // Update status
        setReceiptStatuses((prev) => ({
          ...prev,
          [data.receiptId]: data.status,
        }));

        // Update message if present
        if (data.message) {
          setStatusMessages((prev) => ({
            ...prev,
            [data.receiptId]: data.message || '',
          }));
        }
      }
    });

    return () => {
      unsubscribe();
    };
  }, [isConnected]);

  return (
    <ProcessingStatusContext.Provider
      value={{
        receiptStatuses,
        statusMessages,
        isConnected,
      }}
    >
      {children}
    </ProcessingStatusContext.Provider>
  );
};

export const useProcessingStatus = () => useContext(ProcessingStatusContext);

export default ProcessingStatusContext;
