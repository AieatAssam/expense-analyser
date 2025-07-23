import apiClient from './api';
import { UserProfile, Account } from '../types';

export const userService = {
  // Get user profile including accounts
  getUserProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/api/users/profile');
    return response.data;
  },
  
  // Switch to another account
  switchAccount: async (accountId: string): Promise<{ success: boolean }> => {
    const response = await apiClient.post('/api/users/switch-account', { accountId });
    return response.data;
  },
  
  // Get accounts list
  getAccounts: async (): Promise<Account[]> => {
    const response = await apiClient.get('/api/users/accounts');
    return response.data;
  }
};

export default userService;
