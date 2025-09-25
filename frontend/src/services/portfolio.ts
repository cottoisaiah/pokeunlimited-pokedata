import { apiClient, ApiResponse, PaginatedResponse } from './api';
import { ProductWithPricing } from './products';

export interface PortfolioItem {
  id: string;
  userId: string;
  productId: string;
  quantity: number;
  averageCost: number;
  condition: 'mint' | 'near_mint' | 'lightly_played' | 'moderately_played' | 'heavily_played' | 'damaged';
  purchaseDate?: string;
  notes?: string;
  isPublic: boolean;
  createdAt: string;
  updatedAt: string;
  product?: ProductWithPricing;
}

export interface PortfolioSummary {
  totalItems: number;
  totalValue: number;
  totalCost: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
  topPerformer?: PortfolioItem;
  worstPerformer?: PortfolioItem;
  lastUpdated: string;
}

export interface PortfolioPerformance {
  date: string;
  totalValue: number;
  dailyChange: number;
  dailyChangePercent: number;
}

export interface AddToPortfolioRequest {
  productId: string;
  quantity: number;
  averageCost: number;
  condition: string;
  purchaseDate?: string;
  notes?: string;
}

export interface UpdatePortfolioItemRequest {
  quantity?: number;
  averageCost?: number;
  condition?: string;
  purchaseDate?: string;
  notes?: string;
  isPublic?: boolean;
}

export interface PortfolioFilters {
  condition?: string;
  set?: string;
  rarity?: string;
  minValue?: number;
  maxValue?: number;
  sortBy?: 'name' | 'value' | 'gainLoss' | 'purchaseDate';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  size?: number;
}

export interface PortfolioAlert {
  id: string;
  userId: string;
  portfolioItemId?: string;
  productId?: string;
  alertType: 'price_target' | 'price_drop' | 'price_increase' | 'volume_spike';
  condition: string;
  targetValue: number;
  isActive: boolean;
  lastTriggered?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateAlertRequest {
  portfolioItemId?: string;
  productId?: string;
  alertType: string;
  condition: string;
  targetValue: number;
}

class PortfolioService {
  async getPortfolio(filters: PortfolioFilters = {}): Promise<PaginatedResponse<PortfolioItem>> {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<PortfolioItem>>>(
      '/api/v1/portfolio',
      filters
    );
    return response.data;
  }

  async getPortfolioSummary(): Promise<PortfolioSummary> {
    const response = await apiClient.get<ApiResponse<PortfolioSummary>>('/api/v1/portfolio/summary');
    return response.data;
  }

  async getPortfolioPerformance(days: number = 30): Promise<PortfolioPerformance[]> {
    const response = await apiClient.get<ApiResponse<PortfolioPerformance[]>>(
      '/api/v1/portfolio/performance',
      { days }
    );
    return response.data;
  }

  async addToPortfolio(item: AddToPortfolioRequest): Promise<PortfolioItem> {
    const response = await apiClient.post<ApiResponse<PortfolioItem>>('/api/v1/portfolio', item);
    return response.data;
  }

  async updatePortfolioItem(id: string, updates: UpdatePortfolioItemRequest): Promise<PortfolioItem> {
    const response = await apiClient.put<ApiResponse<PortfolioItem>>(`/api/v1/portfolio/${id}`, updates);
    return response.data;
  }

  async removeFromPortfolio(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/portfolio/${id}`);
  }

  async getPortfolioItem(id: string): Promise<PortfolioItem> {
    const response = await apiClient.get<ApiResponse<PortfolioItem>>(`/api/v1/portfolio/${id}`);
    return response.data;
  }

  async bulkAddToPortfolio(items: AddToPortfolioRequest[]): Promise<PortfolioItem[]> {
    const response = await apiClient.post<ApiResponse<PortfolioItem[]>>('/api/v1/portfolio/bulk', { items });
    return response.data;
  }

  async bulkUpdatePortfolio(updates: Array<{ id: string; updates: UpdatePortfolioItemRequest }>): Promise<PortfolioItem[]> {
    const response = await apiClient.put<ApiResponse<PortfolioItem[]>>('/api/v1/portfolio/bulk', { updates });
    return response.data;
  }

  async bulkDeleteFromPortfolio(ids: string[]): Promise<void> {
    await apiClient.post('/api/v1/portfolio/bulk/delete', { ids });
  }

  // Portfolio Analytics
  async getPortfolioAnalytics(timeframe: '7d' | '30d' | '90d' | '1y' = '30d') {
    const response = await apiClient.get<ApiResponse<any>>('/api/v1/portfolio/analytics', { timeframe });
    return response.data;
  }

  async getPortfolioBySet(): Promise<Array<{ set: string; count: number; value: number }>> {
    const response = await apiClient.get<ApiResponse<Array<{ set: string; count: number; value: number }>>>(
      '/api/v1/portfolio/by-set'
    );
    return response.data;
  }

  async getPortfolioByRarity(): Promise<Array<{ rarity: string; count: number; value: number }>> {
    const response = await apiClient.get<ApiResponse<Array<{ rarity: string; count: number; value: number }>>>(
      '/api/v1/portfolio/by-rarity'
    );
    return response.data;
  }

  async getPortfolioByCondition(): Promise<Array<{ condition: string; count: number; value: number }>> {
    const response = await apiClient.get<ApiResponse<Array<{ condition: string; count: number; value: number }>>>(
      '/api/v1/portfolio/by-condition'
    );
    return response.data;
  }

  // Portfolio Alerts
  async getPortfolioAlerts(): Promise<PortfolioAlert[]> {
    const response = await apiClient.get<ApiResponse<PortfolioAlert[]>>('/api/v1/portfolio/alerts');
    return response.data;
  }

  async createPortfolioAlert(alert: CreateAlertRequest): Promise<PortfolioAlert> {
    const response = await apiClient.post<ApiResponse<PortfolioAlert>>('/api/v1/portfolio/alerts', alert);
    return response.data;
  }

  async updatePortfolioAlert(id: string, updates: Partial<CreateAlertRequest>): Promise<PortfolioAlert> {
    const response = await apiClient.put<ApiResponse<PortfolioAlert>>(`/api/v1/portfolio/alerts/${id}`, updates);
    return response.data;
  }

  async deletePortfolioAlert(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/portfolio/alerts/${id}`);
  }

  async togglePortfolioAlert(id: string): Promise<PortfolioAlert> {
    const response = await apiClient.post<ApiResponse<PortfolioAlert>>(`/api/v1/portfolio/alerts/${id}/toggle`);
    return response.data;
  }

  // Import/Export
  async importPortfolio(file: File): Promise<{ success: number; errors: Array<{ row: number; error: string }> }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${apiClient['baseURL']}/api/v1/portfolio/import`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiClient['token']}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Import failed');
    }

    const result = await response.json();
    return result.data;
  }

  async exportPortfolio(format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await fetch(`${apiClient['baseURL']}/api/v1/portfolio/export`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiClient['token']}`,
        Accept: format === 'csv' ? 'text/csv' : 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  }

  // Portfolio Sharing
  async sharePortfolio(isPublic: boolean): Promise<{ shareUrl?: string }> {
    const response = await apiClient.post<ApiResponse<{ shareUrl?: string }>>(
      '/api/v1/portfolio/share',
      { isPublic }
    );
    return response.data;
  }

  async getSharedPortfolio(shareId: string): Promise<{
    portfolio: PortfolioItem[];
    summary: PortfolioSummary;
    owner: { name: string };
  }> {
    const response = await apiClient.get<ApiResponse<{
      portfolio: PortfolioItem[];
      summary: PortfolioSummary;
      owner: { name: string };
    }>>(`/api/v1/portfolio/shared/${shareId}`);
    return response.data;
  }
}

export const portfolioService = new PortfolioService();