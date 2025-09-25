import { apiClient, ApiResponse } from './api';

export interface User {
  id: string;
  email: string;
  name: string;
  plan: 'free' | 'gold' | 'platinum';
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
  user: User;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
}

class AuthService {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<ApiResponse<AuthResponse>>('/api/v1/auth/login', credentials);
    
    // Set the token in the API client
    apiClient.setToken(response.data.accessToken);
    
    return response.data;
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<ApiResponse<AuthResponse>>('/api/v1/auth/register', userData);
    
    // Set the token in the API client
    apiClient.setToken(response.data.accessToken);
    
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      // Even if the logout request fails, we should clear the local token
      console.warn('Logout request failed:', error);
    } finally {
      // Clear the token from the API client and local storage
      apiClient.setToken(null);
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>('/api/v1/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiClient.post<ApiResponse<AuthResponse>>('/api/v1/auth/refresh');
    
    // Update the token in the API client
    apiClient.setToken(response.data.accessToken);
    
    return response.data;
  }

  async requestPasswordReset(request: PasswordResetRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/password-reset', request);
  }

  async confirmPasswordReset(request: PasswordResetConfirm): Promise<void> {
    await apiClient.post('/api/v1/auth/password-reset/confirm', request);
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await apiClient.put<ApiResponse<User>>('/api/v1/auth/profile', userData);
    return response.data;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/api/v1/auth/change-password', {
      currentPassword,
      newPassword,
    });
  }

  async deleteAccount(): Promise<void> {
    await apiClient.delete('/api/v1/auth/account');
    // Clear the token after account deletion
    apiClient.setToken(null);
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  }

  // Get stored token
  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }
}

export const authService = new AuthService();