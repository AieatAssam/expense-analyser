import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Select,
  Alert,
  Card,
  CardBody,
  CardHeader,
  Heading,
  IconButton,
  Badge,
  Spinner,
} from '@chakra-ui/react';
import { 
  FiSave, 
  FiPlus, 
  FiTrash2, 
  FiX
} from 'react-icons/fi';
import { format } from 'date-fns';

import { receiptEditingService, ReceiptDetailResponse, LineItemResponse } from '../../services/receiptEditingService';

interface ReceiptEditModalProps {
  receiptId: number;
  isOpen: boolean;
  onClose: () => void;
  onSaved: (receiptId: number) => void;
}

interface LineItemFormData {
  id?: number;
  name: string;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category_name: string;
}

interface ReceiptFormData {
  store_name: string;
  receipt_date: string;
  total_amount: number;
  tax_amount: number;
  currency: string;
  receipt_number: string;
  line_items: LineItemFormData[];
  is_verified: boolean;
  verification_notes: string;
}

const mapLineItemToFormData = (item: LineItemResponse): LineItemFormData => ({
  id: item.id,
  name: item.name,
  description: item.description || '',
  quantity: item.quantity,
  unit_price: item.unit_price,
  total_price: item.total_price,
  category_name: item.category_name || '',
});

export const ReceiptEditModal: React.FC<ReceiptEditModalProps> = ({
  receiptId,
  isOpen,
  onClose,
  onSaved,
}) => {
  const [receipt, setReceipt] = useState<ReceiptDetailResponse | null>(null);
  const [formData, setFormData] = useState<ReceiptFormData>({
    store_name: '',
    receipt_date: '',
    total_amount: 0,
    tax_amount: 0,
    currency: 'USD',
    receipt_number: '',
    line_items: [],
    is_verified: false,
    verification_notes: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const loadReceipt = async () => {
    setIsLoading(true);
    try {
      const receiptData = await receiptEditingService.getReceiptForEditing(receiptId);
      setReceipt(receiptData);
      
      // Initialize form data
      setFormData({
        store_name: receiptData.store_name,
        receipt_date: receiptData.receipt_date ? format(new Date(receiptData.receipt_date), 'yyyy-MM-dd') : '',
        total_amount: receiptData.total_amount,
        tax_amount: receiptData.tax_amount || 0,
        currency: receiptData.currency,
        receipt_number: receiptData.receipt_number || '',
        line_items: receiptData.line_items.map(mapLineItemToFormData),
        is_verified: receiptData.is_verified,
        verification_notes: receiptData.verification_notes || '',
      });
    } catch (error) {
      console.error('Error loading receipt:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && receiptId) {
      loadReceipt();
    }
  }, [isOpen, receiptId]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.store_name.trim()) {
      errors.store_name = 'Store name is required';
    }

    if (!formData.receipt_date) {
      errors.receipt_date = 'Receipt date is required';
    }

    if (formData.total_amount <= 0) {
      errors.total_amount = 'Total amount must be greater than 0';
    }

    if (formData.line_items.length === 0) {
      errors.line_items = 'At least one line item is required';
    }

    // Validate line items
    formData.line_items.forEach((item, index) => {
      if (!item.name.trim()) {
        errors[`line_item_${index}_name`] = 'Item name is required';
      }
      if (item.quantity <= 0) {
        errors[`line_item_${index}_quantity`] = 'Quantity must be greater than 0';
      }
      if (item.total_price <= 0) {
        errors[`line_item_${index}_total_price`] = 'Total price must be greater than 0';
      }
    });

    // Validate line items total vs receipt total
    const lineItemsTotal = formData.line_items.reduce((sum, item) => sum + item.total_price, 0);
    const difference = Math.abs(lineItemsTotal - formData.total_amount);
    if (difference > 0.05) {
      errors.total_mismatch = `Line items total (${lineItemsTotal.toFixed(2)}) doesn't match receipt total (${formData.total_amount.toFixed(2)})`;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSaving(true);
    try {
      const editRequest = {
        store_name: formData.store_name,
        receipt_date: formData.receipt_date,
        total_amount: formData.total_amount,
        tax_amount: formData.tax_amount,
        currency: formData.currency,
        receipt_number: formData.receipt_number || undefined,
        line_items: formData.line_items.map(item => ({
          name: item.name,
          description: item.description || undefined,
          quantity: item.quantity,
          unit_price: item.unit_price,
          total_price: item.total_price,
          category_name: item.category_name || undefined,
        })),
        is_verified: formData.is_verified,
        verification_notes: formData.verification_notes || undefined,
      };

      await receiptEditingService.updateReceipt(receiptId, editRequest);

      onSaved(receiptId);
      onClose();
    } catch (error) {
      console.error('Error updating receipt:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [
        ...prev.line_items,
        {
          name: '',
          description: '',
          quantity: 1,
          unit_price: 0,
          total_price: 0,
          category_name: '',
        },
      ],
    }));
  };

  const removeLineItem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index),
    }));
  };

  const updateLineItem = (index: number, field: keyof LineItemFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.map((item, i) => {
        if (i === index) {
          const updatedItem = { ...item, [field]: value };
          
          // Auto-calculate total_price if quantity or unit_price changes
          if (field === 'quantity' || field === 'unit_price') {
            updatedItem.total_price = updatedItem.quantity * updatedItem.unit_price;
          }
          
          return updatedItem;
        }
        return item;
      }),
    }));
  };

  const calculateLineItemsTotal = () => {
    return formData.line_items.reduce((sum, item) => sum + item.total_price, 0);
  };

  if (!isOpen) return null;

  if (isLoading) {
    return (
      <Box
        position="fixed"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="rgba(0,0,0,0.5)"
        display="flex"
        alignItems="center"
        justifyContent="center"
        zIndex="1000"
      >
        <Card>
          <CardBody p={8}>
            <VStack gap={4}>
              <Spinner size="lg" />
              <Text>Loading receipt details...</Text>
            </VStack>
          </CardBody>
        </Card>
      </Box>
    );
  }

  return (
    <Box
      position="fixed"
      top="0"
      left="0"
      right="0"
      bottom="0"
      bg="rgba(0,0,0,0.5)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      zIndex="1000"
      p={4}
    >
      <Box
        bg="white"
        borderRadius="md"
        maxW="6xl"
        maxH="90vh"
        w="full"
        overflow="auto"
      >
        {/* Header */}
        <Box p={4} borderBottom="1px" borderColor="gray.200">
          <HStack justify="space-between" align="center">
            <Text fontSize="lg" fontWeight="bold">Edit Receipt</Text>
            <HStack gap={2}>
              {receipt?.validation_summary && (
                <Badge
                  colorPalette={
                    receipt.validation_summary.validation_result === 'passed' ? 'green' :
                    receipt.validation_summary.validation_result === 'warning' ? 'yellow' : 'red'
                  }
                >
                  Confidence: {(receipt.validation_summary.confidence_score * 100).toFixed(1)}%
                </Badge>
              )}
              <IconButton
                aria-label="Close"
                icon={<FiX />}
                variant="outline"
                size="sm"
                onClick={handleCancel}
              />
            </HStack>
          </HStack>
        </Box>

        {/* Body */}
        <Box p={4}>
          <VStack gap={6} align="stretch">
            {/* Validation Errors */}
            {Object.keys(validationErrors).length > 0 && (
              <Alert status="error">
                <AlertIcon />
                <VStack align="start" gap={1}>
                  <Text fontWeight="medium">Please fix the following errors:</Text>
                  {Object.entries(validationErrors).map(([field, error]) => (
                    <Text key={field} fontSize="sm">• {error}</Text>
                  ))}
                </VStack>
              </Alert>
            )}

            {/* Receipt Basic Information */}
            <Card>
              <CardHeader>
                <Heading size="md">Receipt Information</Heading>
              </CardHeader>
              <CardBody>
                <VStack gap={4} align="stretch">
                  <HStack gap={4}>
                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium" mb={2}>Store Name</Text>
                      <Input
                        value={formData.store_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, store_name: e.target.value }))}
                        placeholder="Enter store name"
                        borderColor={validationErrors.store_name ? 'red.300' : 'gray.200'}
                      />
                      {validationErrors.store_name && (
                        <Text color="red.500" fontSize="sm" mt={1}>{validationErrors.store_name}</Text>
                      )}
                    </Box>

                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium" mb={2}>Receipt Date</Text>
                      <Input
                        type="date"
                        value={formData.receipt_date}
                        onChange={(e) => setFormData(prev => ({ ...prev, receipt_date: e.target.value }))}
                        borderColor={validationErrors.receipt_date ? 'red.300' : 'gray.200'}
                      />
                      {validationErrors.receipt_date && (
                        <Text color="red.500" fontSize="sm" mt={1}>{validationErrors.receipt_date}</Text>
                      )}
                    </Box>
                  </HStack>

                  <HStack gap={4}>
                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium" mb={2}>Total Amount</Text>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.total_amount}
                        onChange={(e) => setFormData(prev => ({ ...prev, total_amount: parseFloat(e.target.value) || 0 }))}
                        borderColor={validationErrors.total_amount ? 'red.300' : 'gray.200'}
                      />
                      {validationErrors.total_amount && (
                        <Text color="red.500" fontSize="sm" mt={1}>{validationErrors.total_amount}</Text>
                      )}
                    </Box>

                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium" mb={2}>Tax Amount</Text>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.tax_amount}
                        onChange={(e) => setFormData(prev => ({ ...prev, tax_amount: parseFloat(e.target.value) || 0 }))}
                      />
                    </Box>

                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium" mb={2}>Currency</Text>
                      <NativeSelectRoot><NativeSelectField
                        value={formData.currency}
                        onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
                      >
                        <option value="USD">USD</option>
                        <option value="EUR">EUR</option>
                        <option value="GBP">GBP</option>
                        <option value="CAD">CAD</option>
                      </NativeSelectField></NativeSelectRoot>
                    </Box>
                  </HStack>

                  <Box>
                    <Text fontSize="sm" fontWeight="medium" mb={2}>Receipt Number (Optional)</Text>
                    <Input
                      value={formData.receipt_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, receipt_number: e.target.value }))}
                      placeholder="Enter receipt number"
                    />
                  </Box>
                </VStack>
              </CardBody>
            </Card>

            {/* Line Items */}
            <Card>
              <CardHeader>
                <HStack justify="space-between" align="center">
                  <Heading size="md">Line Items</Heading>
                  <Button
                    leftIcon={<FiPlus />}
                    onClick={addLineItem}
                    size="sm"
                    colorPalette="blue"
                  >
                    Add Item
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack gap={4} align="stretch">
                  {formData.line_items.map((item, index) => (
                    <Box key={index} p={4} border="1px" borderColor="gray.200" borderRadius="md">
                      <HStack justify="space-between" align="start" gap={4}>
                        <VStack gap={3} align="stretch" flex={1}>
                          <HStack gap={3}>
                            <Box flex={2}>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Item Name</Text>
                              <Input
                                value={item.name}
                                onChange={(e) => updateLineItem(index, 'name', e.target.value)}
                                placeholder="Enter item name"
                                size="sm"
                                borderColor={validationErrors[`line_item_${index}_name`] ? 'red.300' : 'gray.200'}
                              />
                              {validationErrors[`line_item_${index}_name`] && (
                                <Text color="red.500" fontSize="xs" mt={1}>
                                  {validationErrors[`line_item_${index}_name`]}
                                </Text>
                              )}
                            </Box>

                            <Box flex={1}>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Category</Text>
                              <Input
                                value={item.category_name}
                                onChange={(e) => updateLineItem(index, 'category_name', e.target.value)}
                                placeholder="Enter category"
                                size="sm"
                              />
                            </Box>
                          </HStack>

                          <Box>
                            <Text fontSize="sm" fontWeight="medium" mb={2}>Description (Optional)</Text>
                            <Input
                              value={item.description}
                              onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                              placeholder="Enter item description"
                              size="sm"
                            />
                          </Box>

                          <HStack gap={3}>
                            <Box flex={1}>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Quantity</Text>
                              <Input
                                type="number"
                                step="0.01"
                                value={item.quantity}
                                onChange={(e) => updateLineItem(index, 'quantity', parseFloat(e.target.value) || 1)}
                                size="sm"
                                borderColor={validationErrors[`line_item_${index}_quantity`] ? 'red.300' : 'gray.200'}
                              />
                              {validationErrors[`line_item_${index}_quantity`] && (
                                <Text color="red.500" fontSize="xs" mt={1}>
                                  {validationErrors[`line_item_${index}_quantity`]}
                                </Text>
                              )}
                            </Box>

                            <Box flex={1}>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Unit Price</Text>
                              <Input
                                type="number"
                                step="0.01"
                                value={item.unit_price}
                                onChange={(e) => updateLineItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                                size="sm"
                              />
                            </Box>

                            <Box flex={1}>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Total Price</Text>
                              <Input
                                type="number"
                                step="0.01"
                                value={item.total_price}
                                onChange={(e) => updateLineItem(index, 'total_price', parseFloat(e.target.value) || 0)}
                                size="sm"
                                borderColor={validationErrors[`line_item_${index}_total_price`] ? 'red.300' : 'gray.200'}
                              />
                              {validationErrors[`line_item_${index}_total_price`] && (
                                <Text color="red.500" fontSize="xs" mt={1}>
                                  {validationErrors[`line_item_${index}_total_price`]}
                                </Text>
                              )}
                            </Box>
                          </HStack>
                        </VStack>

                        <IconButton
                          aria-label="Remove item"
                          icon={<FiTrash2 />}
                          onClick={() => removeLineItem(index)}
                          variant="outline"
                          colorPalette="red"
                          size="sm"
                        />
                      </HStack>
                    </Box>
                  ))}

                  {formData.line_items.length === 0 && (
                    <Text color="gray.500" textAlign="center" py={4}>
                      No line items. Click "Add Item" to add items to this receipt.
                    </Text>
                  )}

                  {formData.line_items.length > 0 && (
                    <Box p={3} bg="gray.50" borderRadius="md">
                      <HStack justify="space-between">
                        <Text fontWeight="medium">Line Items Total:</Text>
                        <Text fontWeight="bold">${calculateLineItemsTotal().toFixed(2)}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontWeight="medium">Receipt Total:</Text>
                        <Text fontWeight="bold">${formData.total_amount.toFixed(2)}</Text>
                      </HStack>
                      {Math.abs(calculateLineItemsTotal() - formData.total_amount) > 0.01 && (
                        <HStack justify="space-between" color="red.500">
                          <Text fontSize="sm">Difference:</Text>
                          <Text fontSize="sm" fontWeight="bold">
                            ${Math.abs(calculateLineItemsTotal() - formData.total_amount).toFixed(2)}
                          </Text>
                        </HStack>
                      )}
                    </Box>
                  )}

                  {validationErrors.line_items && (
                    <Text color="red.500" fontSize="sm">{validationErrors.line_items}</Text>
                  )}
                  {validationErrors.total_mismatch && (
                    <Alert status="warning" size="sm">
                      <AlertIcon />
                      <Text fontSize="sm">{validationErrors.total_mismatch}</Text>
                    </Alert>
                  )}
                </VStack>
              </CardBody>
            </Card>

            {/* Verification */}
            <Card>
              <CardHeader>
                <Heading size="md">Verification</Heading>
              </CardHeader>
              <CardBody>
                <VStack gap={4} align="stretch">
                  <Box>
                    <HStack align="center">
                      <input
                        type="checkbox"
                        id="is-verified"
                        checked={formData.is_verified}
                        onChange={(e) => setFormData(prev => ({ ...prev, is_verified: e.target.checked }))}
                      />
                      <Text fontSize="sm" fontWeight="medium" ml={2}>Mark as verified</Text>
                    </HStack>
                  </Box>

                  <Box>
                    <Text fontSize="sm" fontWeight="medium" mb={2}>Verification Notes</Text>
                    <textarea
                      value={formData.verification_notes}
                      onChange={(e) => setFormData(prev => ({ ...prev, verification_notes: e.target.value }))}
                      placeholder="Add notes about your verification or changes"
                      rows={3}
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #E2E8F0',
                        borderRadius: '4px',
                        resize: 'vertical'
                      }}
                    />
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </Box>

        {/* Footer */}
        <Box p={4} borderTop="1px" borderColor="gray.200">
          <HStack gap={3} justify="end">
            <Button
              variant="outline"
              onClick={handleCancel}
              isDisabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              colorPalette="blue"
              onClick={handleSave}
              isLoading={isSaving}
              loadingText="Saving..."
              leftIcon={<FiSave />}
            >
              Save Changes
            </Button>
          </HStack>
        </Box>
      </Box>
    </Box>
  );
};
