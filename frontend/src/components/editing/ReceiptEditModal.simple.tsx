import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  NativeSelectRoot,
  NativeSelectField,
  Heading,
  Badge,
  Spinner,
} from '@chakra-ui/react';

interface LineItemData {
  id?: number;
  description: string;
  amount: number;
  category_id?: number;
  category_name?: string;
}

interface ReceiptData {
  id: number;
  vendor: string;
  date: string;
  total_amount: number;
  payment_method?: string;
  notes?: string;
  line_items: LineItemData[];
  validation_status?: string;
  confidence_score?: number;
}

interface ReceiptEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  receiptId: number | null;
  onSave?: () => void;
}

const ReceiptEditModal: React.FC<ReceiptEditModalProps> = ({
  isOpen,
  onClose,
  receiptId,
  onSave
}) => {
  const [receipt, setReceipt] = useState<ReceiptData | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && receiptId) {
      loadReceipt();
    }
  }, [isOpen, receiptId]);

  const loadReceipt = async () => {
    if (!receiptId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Mock data for now - replace with actual service call
      const mockReceipt: ReceiptData = {
        id: receiptId,
        vendor: 'Sample Store',
        date: '2024-01-15',
        total_amount: 25.99,
        payment_method: 'credit_card',
        notes: 'Sample receipt',
        line_items: [
          {
            id: 1,
            description: 'Coffee',
            amount: 4.99,
            category_id: 1,
            category_name: 'Food & Beverage'
          },
          {
            id: 2,
            description: 'Sandwich',
            amount: 12.99,
            category_id: 1,
            category_name: 'Food & Beverage'
          }
        ],
        validation_status: 'needs_review',
        confidence_score: 0.85
      };
      
      setReceipt(mockReceipt);
    } catch (err) {
      setError('Failed to load receipt');
      console.error('Error loading receipt:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!receipt) return;
    
    setSaving(true);
    setError(null);
    
    try {
      // Mock save - replace with actual service call
      console.log('Saving receipt:', receipt);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onSave?.();
      onClose();
    } catch (err) {
      setError('Failed to save receipt');
      console.error('Error saving receipt:', err);
    } finally {
      setSaving(false);
    }
  };

  const updateReceiptField = (field: keyof ReceiptData, value: any) => {
    if (!receipt) return;
    setReceipt(prev => prev ? { ...prev, [field]: value } : null);
  };

  const updateLineItem = (index: number, field: keyof LineItemData, value: any) => {
    if (!receipt) return;
    
    const updatedLineItems = [...receipt.line_items];
    updatedLineItems[index] = { ...updatedLineItems[index], [field]: value };
    
    setReceipt(prev => prev ? { ...prev, line_items: updatedLineItems } : null);
  };

  const addLineItem = () => {
    if (!receipt) return;
    
    const newLineItem: LineItemData = {
      description: '',
      amount: 0,
      category_id: undefined,
      category_name: ''
    };
    
    setReceipt(prev => prev ? {
      ...prev,
      line_items: [...prev.line_items, newLineItem]
    } : null);
  };

  const removeLineItem = (index: number) => {
    if (!receipt) return;
    
    const updatedLineItems = receipt.line_items.filter((_, i) => i !== index);
    setReceipt(prev => prev ? { ...prev, line_items: updatedLineItems } : null);
  };

  if (!isOpen) return null;

  return (
    <Box
      position="fixed"
      top="0"
      left="0"
      width="100%"
      height="100%"
      bg="rgba(0, 0, 0, 0.5)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      zIndex="1000"
    >
      <Box
        bg="white"
        borderRadius="md"
        p="6"
        maxWidth="800px"
        width="90%"
        maxHeight="90%"
        overflow="auto"
      >
        <HStack justifyContent="space-between" mb="4">
          <Heading size="lg">Edit Receipt</Heading>
          <Button variant="outline" onClick={onClose}>
            ×
          </Button>
        </HStack>

        {loading && (
          <Box textAlign="center" py="8">
            <Spinner size="lg" />
            <Text mt="2">Loading receipt...</Text>
          </Box>
        )}

        {error && (
          <Box
            bg="red.50"
            border="1px solid"
            borderColor="red.200"
            borderRadius="md"
            p="4"
            mb="4"
          >
            <Text color="red.700">{error}</Text>
          </Box>
        )}

        {receipt && !loading && (
          <VStack gap="4" align="stretch">
            {/* Validation Status */}
            {receipt.validation_status && (
              <Box>
                <Text fontSize="sm" fontWeight="bold" mb="2">
                  Validation Status
                </Text>
                <HStack>
                  <Badge
                    colorPalette={
                      receipt.validation_status === 'validated' ? 'green' :
                      receipt.validation_status === 'needs_review' ? 'yellow' : 'red'
                    }
                  >
                    {receipt.validation_status.replace('_', ' ')}
                  </Badge>
                  {receipt.confidence_score && (
                    <Text fontSize="sm">
                      Confidence: {Math.round(receipt.confidence_score * 100)}%
                    </Text>
                  )}
                </HStack>
              </Box>
            )}

            {/* Basic Receipt Fields */}
            <Box>
              <Text fontSize="sm" fontWeight="bold" mb="2">Vendor</Text>
              <Input
                value={receipt.vendor}
                onChange={(e) => updateReceiptField('vendor', e.target.value)}
                placeholder="Vendor name"
              />
            </Box>

            <Box>
              <Text fontSize="sm" fontWeight="bold" mb="2">Date</Text>
              <Input
                type="date"
                value={receipt.date}
                onChange={(e) => updateReceiptField('date', e.target.value)}
              />
            </Box>

            <Box>
              <Text fontSize="sm" fontWeight="bold" mb="2">Payment Method</Text>
              <NativeSelectRoot>
                <NativeSelectField
                  value={receipt.payment_method || ''}
                  onChange={(e) => updateReceiptField('payment_method', e.target.value)}
                >
                  <option value="">Select payment method</option>
                  <option value="cash">Cash</option>
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="mobile_payment">Mobile Payment</option>
                  <option value="other">Other</option>
                </NativeSelectField>
              </NativeSelectRoot>
            </Box>

            <Box>
              <Text fontSize="sm" fontWeight="bold" mb="2">Notes</Text>
              <Input
                value={receipt.notes || ''}
                onChange={(e) => updateReceiptField('notes', e.target.value)}
                placeholder="Additional notes"
              />
            </Box>

            {/* Line Items */}
            <Box>
              <HStack justifyContent="space-between" mb="4">
                <Text fontSize="lg" fontWeight="bold">Line Items</Text>
                <Button size="sm" onClick={addLineItem}>
                  + Add Item
                </Button>
              </HStack>

              <VStack gap="3" align="stretch">
                {receipt.line_items.map((item, index) => (
                  <Box
                    key={index}
                    border="1px solid"
                    borderColor="gray.200"
                    borderRadius="md"
                    p="4"
                  >
                    <HStack justifyContent="space-between" mb="3">
                      <Text fontWeight="bold">Item {index + 1}</Text>
                      <Button
                        size="sm"
                        variant="outline"
                        colorPalette="red"
                        onClick={() => removeLineItem(index)}
                      >
                        Remove
                      </Button>
                    </HStack>

                    <VStack gap="3" align="stretch">
                      <Box>
                        <Text fontSize="sm" fontWeight="bold" mb="1">Description</Text>
                        <Input
                          value={item.description}
                          onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                          placeholder="Item description"
                        />
                      </Box>

                      <Box>
                        <Text fontSize="sm" fontWeight="bold" mb="1">Amount</Text>
                        <Input
                          type="number"
                          step="0.01"
                          value={item.amount}
                          onChange={(e) => updateLineItem(index, 'amount', parseFloat(e.target.value) || 0)}
                          placeholder="0.00"
                        />
                      </Box>

                      <Box>
                        <Text fontSize="sm" fontWeight="bold" mb="1">Category</Text>
                        <Input
                          value={item.category_name || ''}
                          onChange={(e) => updateLineItem(index, 'category_name', e.target.value)}
                          placeholder="Category name"
                        />
                      </Box>
                    </VStack>
                  </Box>
                ))}
              </VStack>

              {/* Total */}
              <Box
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                p="4"
                bg="gray.50"
                mt="4"
              >
                <HStack justifyContent="space-between">
                  <Text fontWeight="bold">Total Amount:</Text>
                  <Text fontWeight="bold" fontSize="lg">
                    ${receipt.line_items.reduce((sum, item) => sum + item.amount, 0).toFixed(2)}
                  </Text>
                </HStack>
              </Box>
            </Box>

            {/* Action Buttons */}
            <HStack justifyContent="flex-end" gap="3" pt="4">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                colorPalette="blue"
                onClick={handleSave}
                isLoading={saving}
                loadingText="Saving..."
              >
                Save Changes
              </Button>
            </HStack>
          </VStack>
        )}
      </Box>
    </Box>
  );
};

export default ReceiptEditModal;
