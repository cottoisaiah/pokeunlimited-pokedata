import { apiClient, ApiResponse, PaginatedResponse } from './api';

export interface Product {
  id: string;
  name: string;
  set: string;
  setCode: string;
  cardNumber: string;
  rarity: string;
  artist?: string;
  releaseDate: string;
  imageUrl?: string;
  description?: string;
  pokemonType?: string;
  hp?: number;
  stage?: string;
  evolvesFrom?: string;
  retreatCost?: number;
  weaknesses?: string[];
  resistances?: string[];
  abilities?: Ability[];
  attacks?: Attack[];
  tcgplayerId?: string;
  category: string;
  subcategory?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Ability {
  name: string;
  text: string;
  type: string;
}

export interface Attack {
  name: string;
  cost: string[];
  damage?: string;
  text?: string;
}

export interface ProductSearchParams {
  query?: string;
  set?: string;
  rarity?: string;
  category?: string;
  subcategory?: string;
  pokemonType?: string;
  minPrice?: number;
  maxPrice?: number;
  sortBy?: 'name' | 'price' | 'release_date' | 'updated_at';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  size?: number;
}

export interface PriceData {
  id: string;
  productId: string;
  source: 'tcgplayer' | 'ebay' | 'manual';
  condition: 'mint' | 'near_mint' | 'lightly_played' | 'moderately_played' | 'heavily_played' | 'damaged';
  price: number;
  currency: string;
  availableQuantity?: number;
  lastUpdated: string;
  url?: string;
}

export interface ProductWithPricing {
  product: Product;
  pricing: PriceData[];
  currentPrice?: number;
  priceChange24h?: number;
  priceChangePercent?: number;
}

export interface PriceHistory {
  date: string;
  price: number;
  volume?: number;
  source: string;
}

export interface MarketAnalysis {
  productId: string;
  avgPrice: number;
  medianPrice: number;
  minPrice: number;
  maxPrice: number;
  volume: number;
  volatility: number;
  trend: 'up' | 'down' | 'stable';
  confidence: number;
  lastUpdated: string;
}

class ProductsService {
  async searchProducts(params: ProductSearchParams = {}): Promise<PaginatedResponse<ProductWithPricing>> {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<ProductWithPricing>>>(
      '/api/v1/products/search',
      params
    );
    return response.data;
  }

  async getProduct(id: string): Promise<ProductWithPricing> {
    const response = await apiClient.get<ApiResponse<ProductWithPricing>>(`/api/v1/products/${id}`);
    return response.data;
  }

  async getProductsBySet(setCode: string, params: Omit<ProductSearchParams, 'set'> = {}): Promise<PaginatedResponse<ProductWithPricing>> {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<ProductWithPricing>>>(
      `/api/v1/products/sets/${setCode}`,
      params
    );
    return response.data;
  }

  async getFeaturedProducts(limit: number = 12): Promise<ProductWithPricing[]> {
    const response = await apiClient.get<ApiResponse<ProductWithPricing[]>>(
      '/api/v1/products/featured',
      { limit }
    );
    return response.data;
  }

  async getTrendingProducts(limit: number = 12): Promise<ProductWithPricing[]> {
    const response = await apiClient.get<ApiResponse<ProductWithPricing[]>>(
      '/api/v1/products/trending',
      { limit }
    );
    return response.data;
  }

  async getProductPriceHistory(
    id: string,
    days: number = 30,
    condition?: string
  ): Promise<PriceHistory[]> {
    const response = await apiClient.get<ApiResponse<PriceHistory[]>>(
      `/api/v1/products/${id}/price-history`,
      { days, condition }
    );
    return response.data;
  }

  async getProductMarketAnalysis(id: string): Promise<MarketAnalysis> {
    const response = await apiClient.get<ApiResponse<MarketAnalysis>>(
      `/api/v1/products/${id}/market-analysis`
    );
    return response.data;
  }

  async getSimilarProducts(id: string, limit: number = 8): Promise<ProductWithPricing[]> {
    const response = await apiClient.get<ApiResponse<ProductWithPricing[]>>(
      `/api/v1/products/${id}/similar`,
      { limit }
    );
    return response.data;
  }

  async getProductsByCategory(
    category: string,
    params: Omit<ProductSearchParams, 'category'> = {}
  ): Promise<PaginatedResponse<ProductWithPricing>> {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<ProductWithPricing>>>(
      `/api/v1/products/categories/${category}`,
      params
    );
    return response.data;
  }

  async getAvailableSets(): Promise<string[]> {
    const response = await apiClient.get<ApiResponse<string[]>>('/api/v1/products/sets');
    return response.data;
  }

  async getAvailableRarities(): Promise<string[]> {
    const response = await apiClient.get<ApiResponse<string[]>>('/api/v1/products/rarities');
    return response.data;
  }

  async getAvailableCategories(): Promise<string[]> {
    const response = await apiClient.get<ApiResponse<string[]>>('/api/v1/products/categories');
    return response.data;
  }

  // Advanced search with external sources (Gold/Platinum tier)
  async searchTCGPlayer(query: string, exact: boolean = false): Promise<any[]> {
    const response = await apiClient.get<ApiResponse<any[]>>(
      '/api/v1/search/external/tcgplayer',
      { query, exact }
    );
    return response.data;
  }

  async searchEbay(query: string, condition?: string): Promise<any[]> {
    const response = await apiClient.get<ApiResponse<any[]>>(
      '/api/v1/search/external/ebay',
      { query, condition }
    );
    return response.data;
  }

  // Bulk operations (Platinum tier)
  async bulkPriceCheck(productIds: string[]): Promise<ProductWithPricing[]> {
    const response = await apiClient.post<ApiResponse<ProductWithPricing[]>>(
      '/api/v1/products/bulk-price-check',
      { productIds }
    );
    return response.data;
  }

  async exportProductData(params: ProductSearchParams): Promise<Blob> {
    const response = await fetch(`${apiClient['baseURL']}/api/v1/products/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiClient['token']}`,
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  }
}

export const productsService = new ProductsService();