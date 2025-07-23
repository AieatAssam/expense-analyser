import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FileUpload from '../components/upload/FileUpload';
import { ReceiptProcessingStatus } from '../types';
import receiptService from '../services/receiptService';

// Mock the receiptService
jest.mock('../services/receiptService', () => ({
  uploadReceipt: jest.fn(),
}));

describe('FileUpload Component', () => {
  const mockOnUploadComplete = jest.fn();
  const mockFile = new File(['dummy content'], 'test-receipt.jpg', { type: 'image/jpeg' });
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders file upload area', () => {
    render(<FileUpload onUploadComplete={mockOnUploadComplete} />);
    
    expect(screen.getByText(/Drag & drop your receipt here/i)).toBeInTheDocument();
    expect(screen.getByText(/JPEG, PNG or PDF/i)).toBeInTheDocument();
    expect(screen.getByText('Select File')).toBeInTheDocument();
    expect(screen.getByText('Take Photo')).toBeInTheDocument();
  });

  test('handles file upload successfully', async () => {
    // Mock successful upload
    const mockReceiptId = '123456';
    (receiptService.uploadReceipt as jest.Mock).mockResolvedValueOnce({ receiptId: mockReceiptId });
    
    render(<FileUpload onUploadComplete={mockOnUploadComplete} />);
    
    // Create a mock file and drop event
    const inputEl = screen.getByTestId('file-input');
    
    // Simulate file upload
    fireEvent.change(inputEl, { target: { files: [mockFile] } });
    
    // Check if upload was called with the file
    expect(receiptService.uploadReceipt).toHaveBeenCalledWith(mockFile);
    
    // Wait for the upload to complete
    await waitFor(() => {
      expect(mockOnUploadComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          id: mockReceiptId,
          fileName: mockFile.name,
          status: ReceiptProcessingStatus.PENDING,
        })
      );
    });
    
    // Success message should be displayed
    expect(screen.getByText(/Receipt uploaded successfully/i)).toBeInTheDocument();
  });

  test('handles file upload error', async () => {
    // Mock upload error
    (receiptService.uploadReceipt as jest.Mock).mockRejectedValueOnce(new Error('Upload failed'));
    
    render(<FileUpload onUploadComplete={mockOnUploadComplete} />);
    
    // Create a mock file and drop event
    const inputEl = screen.getByTestId('file-input');
    
    // Simulate file upload
    fireEvent.change(inputEl, { target: { files: [mockFile] } });
    
    // Check if upload was called with the file
    expect(receiptService.uploadReceipt).toHaveBeenCalledWith(mockFile);
    
    // Wait for the error message to be displayed
    await waitFor(() => {
      expect(screen.getByText(/Failed to upload receipt/i)).toBeInTheDocument();
    });
    
    // onUploadComplete should not be called on error
    expect(mockOnUploadComplete).not.toHaveBeenCalled();
  });
});
