import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import StatusDisplay from '../components/status/StatusDisplay';
import { useProcessingStatus } from '../contexts/ProcessingStatusContext';
import receiptService from '../services/receiptService';
import { Receipt, ReceiptProcessingStatus } from '../types';

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
    expect(screen.getByText('Pending processing...')).toBeInTheDocument();
    
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
        receipt={mockReceipt}
        onStatusUpdate={mockOnStatusUpdate}
      />
    );
    
    // Should show the updated status from WebSocket
    expect(screen.getByText('Processing receipt...')).toBeInTheDocument();
    expect(screen.getByText('Processing receipt data...')).toBeInTheDocument();
    
    // Check if the onStatusUpdate callback was called with the new status
    expect(mockOnStatusUpdate).toHaveBeenCalledWith({
      ...mockReceipt,
      status: ReceiptProcessingStatus.PROCESSING,
    });
  });
  
  test('polls for status updates when WebSocket is not available', async () => {
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
    expect(screen.getByText('Pending processing...')).toBeInTheDocument();
    
    // After polling, it should update to the new status
    await waitFor(() => {
      expect(receiptService.getReceiptStatus).toHaveBeenCalledWith('receipt-123');
    });
    
    await waitFor(() => {
      expect(screen.getByText('Processing receipt...')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Processing via API...')).toBeInTheDocument();
    
    // Check if the onStatusUpdate callback was called with the new status
    expect(mockOnStatusUpdate).toHaveBeenCalledWith({
      ...mockReceipt,
      status: ReceiptProcessingStatus.PROCESSING,
    });
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
    expect(screen.getByText('Processing failed')).toBeInTheDocument();
    expect(screen.getByText('Failed to process receipt')).toBeInTheDocument();
  });
});
