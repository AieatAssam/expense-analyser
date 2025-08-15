import React, { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { Box, VStack, HStack, Text, Button, Input } from '@chakra-ui/react';
import { DashboardLayout } from '../components/dashboard';
import { useAuth } from '../contexts/AuthContext';
import receiptEditingService, { ReceiptDetailResponse, ReceiptEditRequest, LineItemEditRequest, LineItemResponse } from '../services/receiptEditingService';
import receiptService from '../services/receiptService';

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
  const [reprocessingId, setReprocessingId] = useState<number | null>(null);

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

  const reprocessReceipt = async (id: number) => {
    try {
      setReprocessingId(id);
      await receiptService.processReceipt(String(id));
      await loadReceipts();
    } catch (e) {
      console.error(e);
      setError('Failed to reprocess receipt');
    } finally {
      setReprocessingId(null);
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


      {/* Receipts table */}
      <Box borderWidth={1} borderColor="gray.200" bg="white" borderRadius="md">
        <Box p={3} borderBottomWidth={1} borderColor="gray.200" fontWeight="semibold">Receipts</Box>
        <Box>
          {/* Table header */}
          <HStack px={3} py={2} borderBottomWidth={1} borderColor="gray.200" fontSize="sm" color="gray.600">
            <Box w="80px">ID</Box>
            <Box flex="1">Store</Box>
            <Box w="130px">Date</Box>
            <Box w="110px" textAlign="right">Total</Box>
            <Box w="150px">Status</Box>
            <Box w="90px">Verified</Box>
            <Box w="220px" textAlign="right">Actions</Box>
          </HStack>

          {/* Table body */}
          <VStack align="stretch" gap={0}>
            {(receipts || []).map((r) => (
              <HStack key={r.id} px={3} py={2} bg="white" _hover={{ bg: '#fafafa' }}>
                <Box w="80px">{r.id}</Box>
                <Box flex="1">{r.store_name || '-'}</Box>
                <Box w="130px">{formatDate(r.receipt_date)}</Box>
                <Box w="110px" textAlign="right">{Number(r.total_amount || 0).toFixed(2)} {r.currency}</Box>
                <Box w="150px">{r.processing_status}</Box>
                <Box w="90px">{r.is_verified ? 'Yes' : 'No'}</Box>
                <Box w="220px" textAlign="right">
                  <HStack justify="flex-end" gap={2}>
                    <Button size="sm" variant="outline" onClick={() => openEditor(r.id)}>View / Edit</Button>
                    <Button size="sm" variant="solid" colorPalette="blue" loading={reprocessingId === r.id} onClick={() => reprocessReceipt(r.id)}>
                      {reprocessingId === r.id ? 'Reprocessing...' : 'Reprocess'}
                    </Button>
                  </HStack>
                </Box>
              </HStack>
            ))}
          </VStack>
        </Box>
      </Box>

      {/* Simple editor panel */}
      {editing && (
        <Box position="fixed" inset={0} bg="blackAlpha.600" display="flex" alignItems="center" justifyContent="center">
          <Box bg="white" borderRadius="md" width="min(100%, 960px)" maxH="90vh" overflowY="auto" boxShadow="lg">
            <HStack justify="space-between" p={3} borderBottomWidth={1} borderColor="gray.200">
              <Text fontWeight="semibold">Edit Receipt #{editing.id}</Text>
              <HStack gap={2}>
                <Button variant="outline" onClick={() => reprocessReceipt(editing.id)} loading={reprocessingId === editing.id}>Reprocess</Button>
                <Button variant="outline" onClick={closeEditor}>Cancel</Button>
                <Button onClick={saveChanges} loading={saving} colorPalette="green">Save</Button>
              </HStack>
            </HStack>

            {/* Minimal fields (display-only for now) */}
            <Box p={4}>
              <VStack align="stretch" gap={3}>
                <HStack gap={3}>
                  <Box flex="1">
                    <Text fontSize="sm" fontWeight="semibold" mb={1}>Store</Text>
                    <Input value={editing.store_name || ''} onChange={(e) => updateField('store_name', e.target.value)} />
                  </Box>
                  <Box w="200px">
                    <Text fontSize="sm" fontWeight="semibold" mb={1}>Date</Text>
                    <Input type="date" value={formatDate(editing.receipt_date)} onChange={(e) => updateField('receipt_date', e.target.value)} />
                  </Box>
                  <Box w="140px">
                    <Text fontSize="sm" fontWeight="semibold" mb={1}>Currency</Text>
                    <Input value={editing.currency || ''} onChange={(e) => updateField('currency', e.target.value)} />
                  </Box>
                </HStack>
              </VStack>
            </Box>
          </Box>
        </Box>
      )}
    </VStack>
  </DashboardLayout>
);

export default ReceiptsPage;
