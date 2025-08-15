import React, { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { Box, VStack, HStack, Text, Button, Input } from '@chakra-ui/react';
import { DashboardLayout } from '../components/dashboard';
import { useAuth } from '../contexts/AuthContext';
import receiptEditingService, { ReceiptDetailResponse, ReceiptEditRequest, LineItemEditRequest, LineItemResponse } from '../services/receiptEditingService';

const formatDate = (iso?: string) => {
  if (!iso) return '';
  try { return new Date(iso).toISOString().slice(0, 10); } catch { return ''; }
};

const ReceiptsPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [receipts, setReceipts] = useState<ReceiptDetailResponse[]>([]);

  const [requiresReviewOnly, setRequiresReviewOnly] = useState(false);
  const [limit, setLimit] = useState(20);
  const [skip, setSkip] = useState(0);

  type EditableLineItem = Partial<LineItemEditRequest & LineItemResponse> & { id?: number };
  type EditableReceipt = Omit<ReceiptDetailResponse, 'line_items'> & { line_items: EditableLineItem[] };

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editing, setEditing] = useState<EditableReceipt | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadReceipts();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, requiresReviewOnly, limit, skip]);

  const loadReceipts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await receiptEditingService.getReceiptsForReview({
        requires_review: requiresReviewOnly,
        skip,
        limit,
      });
      setReceipts(data);
    } catch (e) {
      console.error(e);
      setError('Failed to load receipts');
    } finally {
      setIsLoading(false);
    }
  };

  const openEditor = async (id: number) => {
    setEditingId(id);
    setError(null);
    try {
      const detail = await receiptEditingService.getReceiptForEditing(id);
      const editable: EditableReceipt = { ...detail, line_items: detail.line_items.map(li => ({ ...li })) };
      setEditing(editable);
      // load image
      try {
        const blob = await receiptEditingService.getReceiptImage(id);
        const url = URL.createObjectURL(blob);
        setImageUrl(url);
      } catch {
        setImageUrl(null);
      }
    } catch (e) {
      console.error(e);
      setError('Failed to load receipt details');
      setEditingId(null);
    }
  };

  const closeEditor = () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl(null);
    setEditingId(null);
    setEditing(null);
  };

  const updateField = (field: keyof EditableReceipt, value: any) => {
    setEditing(prev => (prev ? { ...prev, [field]: value } as EditableReceipt : prev));
  };

  const updateLineItem = (index: number, field: keyof LineItemEditRequest, value: any) => {
    setEditing(prev => {
      if (!prev) return prev;
      const items: EditableLineItem[] = [...prev.line_items];
      const updated: EditableLineItem = { ...items[index], [field]: value };
      items[index] = updated;
      return { ...prev, line_items: items } as EditableReceipt;
    });
  };

  const addLineItem = () => {
    setEditing(prev => (prev ? {
      ...prev,
      line_items: [
        ...prev.line_items,
        { name: '', description: '', quantity: 1, unit_price: 0, total_price: 0 } as EditableLineItem,
      ],
    } : prev));
  };

  const removeLineItem = (index: number) => {
    setEditing(prev => {
      if (!prev) return prev;
      const items = prev.line_items.filter((_, i) => i !== index);
      return { ...prev, line_items: items } as EditableReceipt;
    });
  };

  const recalcItemTotal = (index: number) => {
    setEditing(prev => {
      if (!prev) return prev;
      const items: EditableLineItem[] = [...prev.line_items];
      const it = items[index] || {};
      const qty = Number(it.quantity ?? 0) || 0;
      const unit = Number(it.unit_price ?? 0) || 0;
      items[index] = { ...it, total_price: Number((qty * unit).toFixed(2)) };
      return { ...prev, line_items: items } as EditableReceipt;
    });
  };

  const totalFromItems = useMemo(() => {
    if (!editing) return 0;
    return editing.line_items.reduce((s, li) => s + (Number(li.total_price) || 0), 0);
  }, [editing]);

  const saveChanges = async () => {
    if (!editing || !editingId) return;
    setSaving(true);
    setError(null);
    try {
      const payload: ReceiptEditRequest = {
        store_name: editing.store_name,
        receipt_date: editing.receipt_date ? formatDate(editing.receipt_date) : undefined,
        total_amount: editing.total_amount,
        tax_amount: editing.tax_amount,
        currency: editing.currency,
        receipt_number: editing.receipt_number,
        is_verified: editing.is_verified,
        verification_notes: editing.verification_notes,
        line_items: editing.line_items.map(li => ({
          name: li.name ?? '',
          description: li.description ?? '',
          quantity: li.quantity ?? 1,
          unit_price: li.unit_price ?? 0,
          total_price: li.total_price ?? 0,
          category_id: li.category_id,
          category_name: li.category_name,
        })),
      };
      await receiptEditingService.updateReceipt(editingId, payload);
      closeEditor();
      await loadReceipts();
    } catch (e) {
      console.error(e);
      setError('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <DashboardLayout title="Receipts">
        <Text>You must be logged in to view receipts.</Text>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Receipts" isLoading={isLoading}>
      <VStack gap={4} align="stretch">
        {error && (
          <Box borderWidth={1} borderColor="red.300" bg="red.50" p={3} borderRadius="md" color="red.700">
            {error}
          </Box>
        )}

        <HStack justify="space-between">
          <HStack gap={3}>
            <label>
              <input
                type="checkbox"
                checked={requiresReviewOnly}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setRequiresReviewOnly(e.target.checked)}
                style={{ marginRight: 6 }}
              />
              Requires review only
            </label>
            <select
              value={String(limit)}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setLimit(Number(e.target.value))}
              style={{ padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: 6 }}
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </HStack>

          <HStack gap={2}>
            <Button variant="outline" onClick={loadReceipts}>Refresh</Button>
          </HStack>
        </HStack>

        <Box borderWidth={1} borderColor="gray.200" bg="white" borderRadius="md">
          <Box p={3} borderBottomWidth={1} borderColor="gray.200" fontWeight="semibold">Receipts</Box>
          <Box>
            <Box as="table" width="100%" style={{ borderCollapse: 'collapse' }}>
              <Box as="thead" bg="gray.50">
                <Box as="tr">
                  <Box as="th" textAlign="left" p={2}>ID</Box>
                  <Box as="th" textAlign="left" p={2}>Store</Box>
                  <Box as="th" textAlign="left" p={2}>Date</Box>
                  <Box as="th" textAlign="right" p={2}>Total</Box>
                  <Box as="th" textAlign="left" p={2}>Status</Box>
                  <Box as="th" textAlign="left" p={2}>Verified</Box>
                  <Box as="th" textAlign="left" p={2}></Box>
                </Box>
              </Box>
              <Box as="tbody">
                {receipts.map(r => (
                  <Box as="tr" key={r.id} borderTopWidth={1} borderColor="gray.100">
                    <Box as="td" p={2}>{r.id}</Box>
                    <Box as="td" p={2}>{r.store_name || '-'}</Box>
                    <Box as="td" p={2}>{r.receipt_date ? formatDate(r.receipt_date as any) : '-'}</Box>
                    <Box as="td" p={2} textAlign="right">{r.total_amount != null ? `$${Number(r.total_amount).toFixed(2)}` : '-'}</Box>
                    <Box as="td" p={2}>{r.processing_status}</Box>
                    <Box as="td" p={2}>{r.is_verified ? 'Yes' : 'No'}</Box>
                    <Box as="td" p={2}>
                      <Button size="sm" onClick={() => openEditor(r.id)}>View / Edit</Button>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          </Box>
        </Box>
      </VStack>

      {/* Simple overlay editor */}
      {editing && (
        <Box position="fixed" top={0} left={0} w="100%" h="100%" bg="rgba(0,0,0,0.5)" display="flex" alignItems="center" justifyContent="center" zIndex={1000}>
          <Box bg="white" borderRadius="md" p={4} maxW="1000px" w="95%" maxH="90%" overflow="auto" boxShadow="lg">
            <HStack justify="space-between" mb={3}>
              <Text fontSize="lg" fontWeight="bold">Edit Receipt #{editing.id}</Text>
              <Button variant="outline" onClick={closeEditor}>Close</Button>
            </HStack>

            <HStack align="start" gap={4}>
              {imageUrl && (
                <Box flex="1" minW="320px">
                  <Box borderWidth={1} borderColor="gray.200" borderRadius="md" overflow="hidden">
                    <img src={imageUrl} alt="Receipt" style={{ width: '100%', display: 'block' }} />
                  </Box>
                </Box>
              )}

              <Box flex="2">
                <VStack gap={3} align="stretch">
                  <HStack gap={3}>
                    <Box flex="1">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Store Name</Text>
                      <Input value={editing.store_name || ''} onChange={(e) => updateField('store_name', e.target.value)} />
                    </Box>
                    <Box w="200px">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Date</Text>
                      <Input type="date" value={formatDate(editing.receipt_date as any)} onChange={(e) => updateField('receipt_date', e.target.value)} />
                    </Box>
                    <Box w="130px">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Currency</Text>
                      <Input value={editing.currency || ''} onChange={(e) => updateField('currency', e.target.value)} />
                    </Box>
                  </HStack>

                  <HStack gap={3}>
                    <Box w="200px">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Total Amount</Text>
                      <Input type="number" step="0.01" value={editing.total_amount ?? 0} onChange={(e) => updateField('total_amount', Number(e.target.value))} />
                    </Box>
                    <Box w="200px">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Tax Amount</Text>
                      <Input type="number" step="0.01" value={editing.tax_amount ?? 0} onChange={(e) => updateField('tax_amount', Number(e.target.value))} />
                    </Box>
                    <Box flex="1">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Receipt Number</Text>
                      <Input value={editing.receipt_number || ''} onChange={(e) => updateField('receipt_number', e.target.value)} />
                    </Box>
                  </HStack>

                  <HStack gap={3}>
                    <Box w="200px">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Verified</Text>
                      <select
                        value={editing.is_verified ? 'true' : 'false'}
                        onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField('is_verified', e.target.value === 'true')}
                        style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: 6 }}
                      >
                        <option value="false">No</option>
                        <option value="true">Yes</option>
                      </select>
                    </Box>
                    <Box flex="1">
                      <Text fontSize="sm" fontWeight="semibold" mb={1}>Verification Notes</Text>
                      <Input value={editing.verification_notes || ''} onChange={(e) => updateField('verification_notes', e.target.value)} />
                    </Box>
                  </HStack>

                  <Box borderWidth={1} borderColor="gray.200" borderRadius="md">
                    <HStack justify="space-between" p={3} borderBottomWidth={1} borderColor="gray.200">
                      <Text fontWeight="semibold">Line Items</Text>
                      <Button size="sm" onClick={addLineItem}>+ Add Item</Button>
                    </HStack>

                    <VStack align="stretch" p={3} gap={3}>
                      {editing.line_items.map((li, idx) => (
                        <Box key={idx} borderWidth={1} borderColor="gray.100" borderRadius="md" p={3}>
                          <HStack justify="space-between" mb={2}>
                            <Text fontWeight="medium">Item {idx + 1}</Text>
                            <Button size="xs" variant="outline" colorPalette="red" onClick={() => removeLineItem(idx)}>Remove</Button>
                          </HStack>
                          <HStack gap={3} align="start">
                            <Box flex="2">
                              <Text fontSize="sm" fontWeight="semibold" mb={1}>Name</Text>
                              <Input value={li.name || ''} onChange={(e) => updateLineItem(idx, 'name', e.target.value)} />
                            </Box>
                            <Box flex="2">
                              <Text fontSize="sm" fontWeight="semibold" mb={1}>Description</Text>
                              <Input value={li.description || ''} onChange={(e) => updateLineItem(idx, 'description', e.target.value)} />
                            </Box>
                          </HStack>
                          <HStack gap={3} mt={2}>
                            <Box w="120px">
                              <Text fontSize="sm" fontWeight="semibold" mb={1}>Quantity</Text>
                              <Input type="number" step="0.01" value={li.quantity ?? 1} onChange={(e) => { updateLineItem(idx, 'quantity', Number(e.target.value)); recalcItemTotal(idx); }} />
                            </Box>
                            <Box w="140px">
                              <Text fontSize="sm" fontWeight="semibold" mb={1}>Unit Price</Text>
                              <Input type="number" step="0.01" value={li.unit_price ?? 0} onChange={(e) => { updateLineItem(idx, 'unit_price', Number(e.target.value)); recalcItemTotal(idx); }} />
                            </Box>
                            <Box w="140px">
                              <Text fontSize="sm" fontWeight="semibold" mb={1}>Total</Text>
                              <Input type="number" step="0.01" value={li.total_price ?? 0} onChange={(e) => updateLineItem(idx, 'total_price', Number(e.target.value))} />
                            </Box>
                            <Box flex="2">
                              <Text fontSize="sm" fontWeight="semibold" mb={1}>Category</Text>
                              <Input value={li.category_name || ''} onChange={(e) => updateLineItem(idx, 'category_name', e.target.value)} />
                            </Box>
                          </HStack>
                        </Box>
                      ))}

                      <Box bg="gray.50" borderRadius="md" p={3} borderWidth={1} borderColor="gray.200">
                        <HStack justify="space-between">
                          <Text fontWeight="semibold">Items Total</Text>
                          <Text fontWeight="bold">${totalFromItems.toFixed(2)}</Text>
                        </HStack>
                      </Box>
                    </VStack>
                  </Box>

                  <HStack justify="flex-end" gap={2}>
                    <Button variant="outline" onClick={closeEditor}>Cancel</Button>
                    <Button onClick={saveChanges} disabled={saving}>{saving ? 'Saving…' : 'Save Changes'}</Button>
                  </HStack>
                </VStack>
              </Box>
            </HStack>
          </Box>
        </Box>
      )}
    </DashboardLayout>
  );
};

export default ReceiptsPage;
