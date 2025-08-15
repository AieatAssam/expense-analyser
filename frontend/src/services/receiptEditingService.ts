import apiClient from './api';

export interface LineItemResponse {
  id: number;
  name: string;
  description?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category_id?: number;
  category_name?: string;
}

export interface ReceiptDetailResponse {
  id: number;
  store_name: string;
  receipt_date?: string;
  total_amount: number;
  tax_amount?: number;
  currency: string;
  receipt_number?: string;
  processing_status: string;
  is_verified: boolean;
  verification_notes?: string;
  image_format?: string;
  line_items: LineItemResponse[];
  validation_summary?: {
    validation_result: string;
    confidence_score: number;
    total_validations: number;
    failed_count: number;
    warning_count: number;
    passed_count: number;
  };
  created_at: string;
  updated_at: string;
}

export interface LineItemEditRequest {
  name: string;
  description?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category_id?: number;
  category_name?: string;
}

export interface ReceiptEditRequest {
  store_name?: string;
  receipt_date?: string;
  total_amount?: number;
  tax_amount?: number;
  currency?: string;
  receipt_number?: string;
  line_items?: LineItemEditRequest[];
  is_verified?: boolean;
  verification_notes?: string;
}

export interface ReceiptEditResponse {
  success: boolean;
  message: string;
  receipt_id?: number;
  validation_result?: string;
  confidence_score?: number;
}

export interface BulkEditRequest {
  receipt_ids: number[];
  operation: 'approve' | 'reject' | 'assign_category';
  category_name?: string;
  notes?: string;
}

export const receiptEditingService = {
  // Get receipt details for editing
  getReceiptForEditing: async (receiptId: number): Promise<ReceiptDetailResponse> => {
    const response = await apiClient.get(`/receipts/edit/${receiptId}`);
    return response.data;
  },

  // Update receipt
  updateReceipt: async (receiptId: number, editRequest: ReceiptEditRequest): Promise<ReceiptEditResponse> => {
    const response = await apiClient.put(`/receipts/edit/${receiptId}`, editRequest);
    return response.data;
  },

  // Bulk edit receipts
  bulkEditReceipts: async (bulkRequest: BulkEditRequest): Promise<ReceiptEditResponse> => {
    const response = await apiClient.post('/receipts/edit/bulk-edit', bulkRequest);
    return response.data;
  },

  // Get receipts requiring review
  getReceiptsForReview: async (params?: {
    status?: string;
    requires_review?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<ReceiptDetailResponse[]> => {
    const response = await apiClient.get('/receipts/edit/', { params });
    return response.data;
  },

  // Get receipt image
  getReceiptImage: async (receiptId: number): Promise<Blob> => {
    const response = await apiClient.get(`/receipts/edit/${receiptId}/image`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default receiptEditingService;
