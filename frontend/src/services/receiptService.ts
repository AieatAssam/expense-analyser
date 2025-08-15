import apiClient from './api';
import { Receipt } from '../types';

export const receiptService = {
  // Upload receipt
  uploadReceipt: async (file: File): Promise<{ receiptId: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/receipts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    // Backend returns snake_case keys at top-level per FileUploadResponse
    const receiptId = String(response.data?.receipt_id ?? '');
    return { receiptId };
  },
  
  // Get receipt by ID
  getReceiptById: async (id: string): Promise<Receipt> => {
    const response = await apiClient.get(`/receipts/${id}`);
    return response.data;
  },
  
  // Get receipt status
  getReceiptStatus: async (id: string): Promise<{ status: string, message?: string }> => {
    const response = await apiClient.get(`/receipts/${id}/processing/status`);
    const data = response.data;
    return {
      status: data?.current_status,
      message: data?.latest_event?.message,
    };
  },
  
  // List receipts
  listReceipts: async (page: number = 1, limit: number = 10): Promise<{ receipts: Receipt[], total: number }> => {
    const response = await apiClient.get('/receipts', {
      params: { page, limit }
    });
    return response.data;
  }
};

export default receiptService;
