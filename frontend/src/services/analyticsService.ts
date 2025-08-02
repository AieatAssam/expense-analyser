import api from './api';

export interface CategorySummary {
  category_id?: number;
  category_name?: string;
  total_amount: number;
  item_count: number;
}

export interface MonthlySummary {
  year: number;
  month: number;
  total_amount: number;
  receipt_count: number;
  categories: CategorySummary[];
}

export interface SpendingTrend {
  date: string;
  amount: number;
  receipt_count: number;
}

export interface ReceiptSummary {
  id: number;
  store_name: string;
  receipt_date: string;
  total_amount: number;
  currency: string;
  processing_status: string;
  is_verified: boolean;
  line_item_count: number;
}

export interface AnalyticsSummary {
  total_receipts: number;
  total_amount: number;
  average_receipt_amount: number;
  date_range: {
    earliest?: string;
    latest?: string;
  };
  top_categories: CategorySummary[];
  recent_activity: ReceiptSummary[];
}

export interface ReceiptListResponse {
  success: boolean;
  message: string;
  data: ReceiptSummary[];
  total_count: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface AnalyticsQuery {
  start_date?: string;
  end_date?: string;
  category_ids?: number[];
  min_amount?: number;
  max_amount?: number;
}

export interface ReceiptListQuery extends AnalyticsQuery {
  search?: string;
  sort_by?: 'receipt_date' | 'total_amount' | 'store_name' | 'created_at';
  sort_order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export class AnalyticsService {
  async getMonthlySummary(year: number, month: number): Promise<MonthlySummary> {
    const response = await api.get(`/analytics/monthly-summary/${year}/${month}`);
    return response.data.data;
  }

  async getCategoryBreakdown(query?: AnalyticsQuery): Promise<CategorySummary[]> {
    const response = await api.get('/analytics/category-breakdown', { params: query });
    return response.data.data;
  }

  async getSpendingTrends(query?: AnalyticsQuery, groupBy: 'day' | 'week' | 'month' = 'day'): Promise<SpendingTrend[]> {
    const response = await api.get('/analytics/spending-trends', { 
      params: { ...query, group_by: groupBy } 
    });
    return response.data.data;
  }

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await api.get('/analytics/summary');
    return response.data;
  }

  async getReceipts(query?: ReceiptListQuery): Promise<ReceiptListResponse> {
    const response = await api.get('/analytics/receipts', { params: query });
    return response.data;
  }

  async getReceiptDetails(receiptId: number): Promise<any> {
    const response = await api.get(`/analytics/receipts/${receiptId}`);
    return response.data;
  }
}

export const analyticsService = new AnalyticsService();