import apiClient from './api';
import { Receipt } from '../types';

export const receiptService = {
  // Upload receipt
  uploadReceipt: async (file: File): Promise<{ receiptId: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/api/receipts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  // Get receipt by ID
  getReceiptById: async (id: string): Promise<Receipt> => {
    const response = await apiClient.get(`/api/receipts/${id}`);
    return response.data;
  },
  
  // Get receipt status
  getReceiptStatus: async (id: string): Promise<{ status: string, message?: string }> => {
    const response = await apiClient.get(`/api/receipts/${id}/status`);
    return response.data;
  },
  
  // List receipts
  listReceipts: async (page: number = 1, limit: number = 10): Promise<{ receipts: Receipt[], total: number }> => {
    const response = await apiClient.get('/api/receipts', {
      params: { page, limit }
    });
    return response.data;
  }
};

export default receiptService;
