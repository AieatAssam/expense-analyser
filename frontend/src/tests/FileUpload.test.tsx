import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import FileUpload from '../components/upload/FileUpload';
import { ReceiptProcessingStatus } from '../types';
import receiptService from '../services/receiptService';

// Mock the receiptService
jest.mock('../services/receiptService', () => ({
  uploadReceipt: jest.fn(),
}));

// Mock the react-dropzone module
jest.mock('react-dropzone', () => ({
  useDropzone: ({ onDrop }: { onDrop: (files: File[]) => void }) => {
    return {
      getRootProps: () => ({
        onClick: () => {
          // This mimics the file selection
          const mockFile = new File(['dummy content'], 'test-receipt.jpg', { type: 'image/jpeg' });
          onDrop([mockFile]);
        }
      }),
      getInputProps: () => ({
        'data-testid': 'file-input',
      }),
      isDragActive: false,
      isDragAccept: false,
      isDragReject: false,
      open: jest.fn(),
    };
  },
}));

describe('FileUpload Component', () => {
  const mockOnUploadComplete = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders file upload area', () => {
    render(<FileUpload onUploadComplete={mockOnUploadComplete} />);
    
    expect(screen.getByText(/Drag & drop your receipt here/i)).toBeInTheDocument();
    expect(screen.getByText(/JPEG, PNG or PDF/i)).toBeInTheDocument();
    expect(screen.getByText(/Select File/i)).toBeInTheDocument();
    expect(screen.getByText(/Take Photo/i)).toBeInTheDocument();
  });

  test('handles file upload successfully', async () => {
    // Mock successful upload
    const mockReceiptId = '123456';
    (receiptService.uploadReceipt as jest.Mock).mockResolvedValueOnce({ receiptId: mockReceiptId });
    
    render(<FileUpload onUploadComplete={mockOnUploadComplete} />);
    
    // The click event and file upload are handled by our mock
    const dropzone = screen.getByText(/Drag & drop your receipt here/i);
    fireEvent.click(dropzone);
    
    // Wait for the upload to complete
    await waitFor(() => {
      expect(mockOnUploadComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          id: mockReceiptId,
          fileName: 'test-receipt.jpg',
          status: ReceiptProcessingStatus.PENDING,
        })
      );
    });
    
    // Success message should be displayed
    await waitFor(() => {
      expect(screen.getByText(/Receipt uploaded successfully/i)).toBeInTheDocument();
    });
  });

  test('handles file upload error', async () => {
    // Mock upload error
    (receiptService.uploadReceipt as jest.Mock).mockRejectedValueOnce(new Error('Upload failed'));
    
    render(<FileUpload onUploadComplete={mockOnUploadComplete} />);
    
    // The click event and file upload are handled by our mock
    const dropzone = screen.getByText(/Drag & drop your receipt here/i);
    fireEvent.click(dropzone);
    
    // Wait for the error message to be displayed
    await waitFor(() => {
      expect(screen.getByText(/Failed to upload receipt/i)).toBeInTheDocument();
    });
    
    // onUploadComplete should not be called on error
    expect(mockOnUploadComplete).not.toHaveBeenCalled();
  });
});
