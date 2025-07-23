// Common types used across the application

export interface User {
  id: string;
  email: string;
  name?: string;
  picture?: string;
}

export interface Account {
  id: string;
  name: string;
}

export interface UserProfile {
  user: User;
  accounts: Account[];
  currentAccount: Account;
}

export enum ReceiptProcessingStatus {
  UPLOADING = 'uploading',
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error'
}

export interface Receipt {
  id: string;
  fileName: string;
  uploadDate: string;
  status: ReceiptProcessingStatus;
  storeName?: string;
  receiptDate?: string;
  totalAmount?: number;
  imageUrl?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}
