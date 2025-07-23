import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import StatusDisplay from '../components/status/StatusDisplay';
import { useProcessingStatus } from '../contexts/ProcessingStatusContext';
import receiptService from '../services/receiptService';
import { Receipt, ReceiptProcessingStatus } from '../types';

// Mock Chakra UI components
jest.mock('@chakra-ui/react', () => {
  return {
    __esModule: true,
    Box: ({ children, ...props }: any) => <div data-testid="chakra-box" {...props}>{children}</div>,
    Text: ({ children, ...props }: any) => <div data-testid="chakra-text" {...props}>{children}</div>,
    Flex: ({ children, ...props }: any) => <div data-testid="chakra-flex" {...props}>{children}</div>,
    Icon: ({ as, ...props }: any) => <div data-testid="chakra-icon" {...props} />,
  };
});

// Mock dependencies
jest.mock('../contexts/ProcessingStatusContext', () => ({
  useProcessingStatus: jest.fn(),
}));

jest.mock('../services/receiptService', () => ({
  getReceiptStatus: jest.fn(),
}));

describe('StatusDisplay Component', () => {
  const mockReceipt: Receipt = {
    id: 'receipt-123',
    fileName: 'test-receipt.jpg',
    uploadDate: '2025-07-23T10:00:00.000Z',
    status: ReceiptProcessingStatus.PENDING,
  };
  
  const mockOnStatusUpdate = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock for ProcessingStatusContext
    (useProcessingStatus as jest.Mock).mockReturnValue({
      receiptStatuses: {},
      statusMessages: {},
      isConnected: false,
    });
    
    // Default mock for getReceiptStatus
    (receiptService.getReceiptStatus as jest.Mock).mockResolvedValue({
      status: ReceiptProcessingStatus.PENDING,
    });
  });
  
  test('renders receipt status with pending state', () => {
    render(
      <StatusDisplay
        receipt={mockReceipt}
        onStatusUpdate={mockOnStatusUpdate}
      />
    );
    
    // Check if the component renders correctly
    expect(screen.getByText('test-receipt.jpg')).toBeInTheDocument();
    
    // Check for status indicator using data-testid and contains text
    const statusElements = screen.getAllByText(/Pending processing/i);
    expect(statusElements.length).toBeGreaterThan(0);
    
    // Date should be displayed
    const dateText = new Date(mockReceipt.uploadDate).toLocaleString();
    expect(screen.getByText(dateText)).toBeInTheDocument();
  });
  
  test('updates status from WebSocket', () => {
    // Mock WebSocket status update
    (useProcessingStatus as jest.Mock).mockReturnValue({
      receiptStatuses: {
        'receipt-123': ReceiptProcessingStatus.PROCESSING,
      },
      statusMessages: {
        'receipt-123': 'Processing receipt data...',
      },
      isConnected: true,
    });
    
    render(
      <StatusDisplay
        receipt={{ ...mockReceipt, status: ReceiptProcessingStatus.PROCESSING }}
        onStatusUpdate={mockOnStatusUpdate}
      />
    );
    
    // Should show the updated status from WebSocket
    const processingElements = screen.getAllByText(/Processing receipt/i);
    expect(processingElements.length).toBeGreaterThan(0);
    
    // Check if the onStatusUpdate callback was called with the new status
    expect(mockOnStatusUpdate).toHaveBeenCalledWith({
      ...mockReceipt,
      status: ReceiptProcessingStatus.PROCESSING,
    });
  });
  
  test('polls for status updates when WebSocket is not available', async () => {
    // Setup timer mocks
    jest.useFakeTimers();
    
    // Mock API response for status update
    (receiptService.getReceiptStatus as jest.Mock).mockResolvedValueOnce({
      status: ReceiptProcessingStatus.PROCESSING,
      message: 'Processing via API...',
    });
    
    render(
      <StatusDisplay
        receipt={mockReceipt}
        onStatusUpdate={mockOnStatusUpdate}
      />
    );
    
    // Initially it should show the pending status
    const pendingElements = screen.getAllByText(/Pending processing/i);
    expect(pendingElements.length).toBeGreaterThan(0);
    
    // Force the polling interval to execute
    // Advance timers to trigger the first polling interval
    jest.advanceTimersByTime(5000);
    
    // Need to use waitFor to wait for async operations inside the effect
    await waitFor(() => {
      expect(receiptService.getReceiptStatus).toHaveBeenCalledWith('receipt-123');
    });
    
    // Check if the onStatusUpdate callback was called with the new status
    expect(mockOnStatusUpdate).toHaveBeenCalledWith({
      ...mockReceipt,
      status: ReceiptProcessingStatus.PROCESSING,
    });
    
    // Restore timer mocks
    jest.useRealTimers();
  });
  
  test('displays error status correctly', () => {
    const errorReceipt = {
      ...mockReceipt,
      status: ReceiptProcessingStatus.ERROR,
    };
    
    (useProcessingStatus as jest.Mock).mockReturnValue({
      receiptStatuses: {
        'receipt-123': ReceiptProcessingStatus.ERROR,
      },
      statusMessages: {
        'receipt-123': 'Failed to process receipt',
      },
      isConnected: true,
    });
    
    render(
      <StatusDisplay
        receipt={errorReceipt}
        onStatusUpdate={mockOnStatusUpdate}
      />
    );
    
    // Should show the error status
    const errorStatusElements = screen.getAllByText(/Processing failed/i);
    expect(errorStatusElements.length).toBeGreaterThan(0);
    expect(screen.getByText('Failed to process receipt')).toBeInTheDocument();
  });
});
