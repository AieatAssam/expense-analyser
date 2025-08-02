import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReceiptEditModal from '../ReceiptEditModal';

const mockProps = {
  isOpen: true,
  onClose: jest.fn(),
  receiptId: 1,
  onSave: jest.fn()
};

describe('ReceiptEditModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders modal when open', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    expect(screen.getByText('Edit Receipt')).toBeInTheDocument();
    
    // Wait for loading to complete and data to be displayed
    await waitFor(() => {
      expect(screen.getByDisplayValue('Sample Store')).toBeInTheDocument();
    });
  });

  test('does not render when closed', () => {
    render(<ReceiptEditModal {...mockProps} isOpen={false} />);
    
    expect(screen.queryByText('Edit Receipt')).not.toBeInTheDocument();
  });

  test('displays receipt data after loading', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Sample Store')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2024-01-15')).toBeInTheDocument();
      expect(screen.getByText('Line Items')).toBeInTheDocument();
    });
  });

  test('allows editing vendor name', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      const vendorInput = screen.getByDisplayValue('Sample Store');
      fireEvent.change(vendorInput, { target: { value: 'New Store Name' } });
      expect(vendorInput).toHaveValue('New Store Name');
    });
  });

  test('can add new line item', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      const addButton = screen.getByText('+ Add Item');
      fireEvent.click(addButton);
      
      // Should now have 3 items (2 original + 1 new)
      expect(screen.getByText('Item 3')).toBeInTheDocument();
    });
  });

  test('can remove line item', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      const removeButtons = screen.getAllByText('Remove');
      fireEvent.click(removeButtons[0]);
      
      // Should now have only 1 item
      expect(screen.queryByText('Item 2')).not.toBeInTheDocument();
    });
  });

  test('calls onClose when cancel is clicked', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);
      expect(mockProps.onClose).toHaveBeenCalled();
    });
  });

  test('calls onSave when save is clicked', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    // Wait for the component to be fully rendered
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });

    // Click the save button
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    // Wait for the save operation to complete with a longer timeout
    await waitFor(() => {
      expect(mockProps.onSave).toHaveBeenCalled();
      expect(mockProps.onClose).toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  test('updates total when line item amounts change', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      const amountInputs = screen.getAllByDisplayValue('4.99');
      fireEvent.change(amountInputs[0], { target: { value: '10.00' } });
      
      // Total should update to reflect the change (10.00 + 12.99 = 22.99)
      expect(screen.getByText('$22.99')).toBeInTheDocument();
    });
  });

  test('displays validation status badge', async () => {
    render(<ReceiptEditModal {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('needs review')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
    });
  });
});
