import api from './api';

export interface ExportQuery {
  start_date?: string;
  end_date?: string;
  include_line_items?: boolean;
}

export interface ExportInfo {
  success: boolean;
  message: string;
  filename: string;
  records_count: number;
  date_range: string;
}

export class ExportService {
  async getExportInfo(query: ExportQuery): Promise<ExportInfo> {
    const response = await api.post('/export/excel/info', query);
    return response.data;
  }

  async downloadExcel(query: ExportQuery): Promise<void> {
    try {
      const params = new URLSearchParams();
      
      if (query.start_date) {
        params.append('start_date', query.start_date);
      }
      if (query.end_date) {
        params.append('end_date', query.end_date);
      }
      if (query.include_line_items !== undefined) {
        params.append('include_line_items', query.include_line_items.toString());
      }

      const response = await api.get(`/export/excel?${params.toString()}`, {
        responseType: 'blob',
        headers: {
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        },
      });

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'expense_export.xlsx';
      
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
        if (fileNameMatch) {
          filename = fileNameMatch[1];
        }
      }

      // Create blob and download
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error downloading Excel file:', error);
      throw new Error('Failed to download Excel file');
    }
  }

  async downloadExcelWithProgress(
    query: ExportQuery,
    onProgress?: (progress: number) => void
  ): Promise<void> {
    try {
      const params = new URLSearchParams();
      
      if (query.start_date) {
        params.append('start_date', query.start_date);
      }
      if (query.end_date) {
        params.append('end_date', query.end_date);
      }
      if (query.include_line_items !== undefined) {
        params.append('include_line_items', query.include_line_items.toString());
      }

      const response = await api.get(`/export/excel?${params.toString()}`, {
        responseType: 'blob',
        headers: {
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        },
        onDownloadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      });

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'expense_export.xlsx';
      
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
        if (fileNameMatch) {
          filename = fileNameMatch[1];
        }
      }

      // Create blob and download
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      if (onProgress) {
        onProgress(100);
      }
      
    } catch (error) {
      console.error('Error downloading Excel file:', error);
      throw new Error('Failed to download Excel file');
    }
  }
}

export const exportService = new ExportService();