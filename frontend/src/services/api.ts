const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = {
        message: response.statusText,
        status: response.status,
      };

      try {
        const errorData = await response.json();
        error.message = errorData.detail || errorData.message || error.message;
        error.details = errorData;
      } catch {
        // If response is not JSON, use the statusText
      }

      throw error;
    }

    try {
      return await response.json();
    } catch {
      // If response is empty, return null
      return null as T;
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(`${this.baseURL}${endpoint}`);
    
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          url.searchParams.append(key, String(params[key]));
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    return this.handleResponse<T>(response);
  }
}

export const apiClient = new ApiClient();

// TCGdex API interfaces
export interface TCGSet {
  id: string;
  name: string;
  logo: string;
  symbol: string;
  releaseDate: string;
  totalCards: number;
  series: string;
  legal: {
    standard: boolean;
    expanded: boolean;
  };
}

export interface TCGCard {
  id: string;
  name: string;
  image: string;
  localId: string;
  illustrator: string;
  rarity: string;
  category: string;
  set: {
    id: string;
    name: string;
  };
  variants?: any[];
  hp?: number;
  types?: string[];
  evolveFrom?: string;
  description?: string;
  level?: string;
  stage?: string;
  attacks?: any[];
  weaknesses?: any[];
  resistances?: any[];
  retreat?: number;
  regulationMark?: string;
  legal?: {
    standard: boolean;
    expanded: boolean;
  };
  // Additional properties for display
  number?: string;
  price?: number;
}

// TCGdex API service functions
export const tcgdexApi = {
  async getSets(lang: string = 'en'): Promise<TCGSet[]> {
    try {
      // Use PokeData API which supports multi-language from database
      const response = await apiClient.get<{ data: any[]; total: number; language: string }>('/api/v1/pokedata/sets', {
        lang: lang,
        limit: 1000 // Get all sets
      });
      
      // Transform the response to match TCGSet interface
      return response.data.map((set: any) => ({
        id: set.tcgdex_id,
        name: set.name,
        logo: set.logo_url,
        symbol: set.symbol_url || '',
        releaseDate: set.release_date || '',
        totalCards: set.total_cards || 0,
        series: set.series_name || '',
        legal: { standard: true, expanded: true }
      }));
    } catch (error) {
      console.error('Failed to fetch sets:', error);
      return [];
    }
  },

  async getSetCards(setId: string, lang: string = 'en'): Promise<TCGCard[]> {
    try {
      // Use PokeData API which supports multi-language from database
      const response = await apiClient.get<{ data: any[]; total: number; language: string }>(`/api/v1/pokedata/cards`, {
        set_id: setId,
        lang: lang,
        limit: 1000 // Get all cards for the set
      });
      
      // Transform the response to match TCGCard interface
      return response.data.map((card: any) => ({
        id: card.tcgdex_id,
        name: card.name,
        image: card.image_url,
        localId: card.local_id || '',
        illustrator: card.illustrator || '',
        rarity: card.rarity || '',
        category: card.category || '',
        set: {
          id: card.set_id,
          name: card.set_name || ''
        },
        hp: card.hp,
        types: card.types || [],
        evolveFrom: card.evolves_from,
        stage: card.stage,
        retreat: card.retreat_cost,
        price: 0 // TODO: Add pricing data
      }));
    } catch (error) {
      console.error(`Failed to fetch cards for set ${setId}:`, error);
      return [];
    }
  },

  async getSetDetails(setId: string, lang: string = 'en'): Promise<TCGSet> {
    try {
      // Use PokeData API which supports multi-language from database
      const response = await apiClient.get<{ data: any }>(`/api/v1/pokedata/sets/${setId}`, {
        lang: lang
      });
      
      const set = response.data;
      return {
        id: set.tcgdex_id,
        name: set.name,
        logo: set.logo_url,
        symbol: set.symbol_url || '',
        releaseDate: set.release_date || '',
        totalCards: set.total_cards || 0,
        series: set.series_name || '',
        legal: { standard: true, expanded: true }
      };
    } catch (error) {
      console.error(`Failed to fetch set details for ${setId}:`, error);
      throw error;
    }
  }
};