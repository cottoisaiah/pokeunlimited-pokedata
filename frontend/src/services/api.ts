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
  async getSets(): Promise<TCGSet[]> {
    try {
      const response = await apiClient.get<{ status: string; data: TCGSet[] }>('/api/v1/tcgdex/sets');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch TCGdex sets:', error);
      // Return mock data as fallback
      return [
        {
          id: 'sv7',
          name: 'White Flare',
          logo: 'https://assets.pokemon.com/assets/cms2/img/cards/web/SV7/SV7_EN_1.png',
          symbol: 'https://assets.pokemon.com/assets/cms2/img/cards/web/SV7/symbol.png',
          releaseDate: '2025-01-17',
          totalCards: 64,
          series: 'Scarlet & Violet',
          legal: { standard: true, expanded: true }
        },
        {
          id: 'sv6',
          name: 'Black Volt',
          logo: 'https://assets.pokemon.com/assets/cms2/img/cards/web/SV6/SV6_EN_1.png',
          symbol: 'https://assets.pokemon.com/assets/cms2/img/cards/web/SV6/symbol.png',
          releaseDate: '2024-11-08',
          totalCards: 66,
          series: 'Scarlet & Violet',
          legal: { standard: true, expanded: true }
        }
      ];
    }
  },

  async getSetCards(setId: string): Promise<TCGCard[]> {
    try {
      const response = await apiClient.get<{ status: string; data: TCGCard[] }>(`/api/v1/tcgdex/sets/${setId}/cards`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch cards for set ${setId}:`, error);
      // Return mock data as fallback
      return [
        {
          id: 'sv7-1',
          name: 'Pikachu',
          image: 'https://assets.pokemon.com/assets/cms2/img/cards/web/SV7/SV7_EN_1.png',
          localId: '1',
          illustrator: 'Mitsuhiro Arita',
          rarity: 'Common',
          category: 'Pokemon',
          set: { id: 'sv7', name: 'White Flare' },
          hp: 60,
          types: ['Lightning'],
          attacks: [{ name: 'Thunder Shock', damage: 20 }],
          weaknesses: [{ type: 'Fighting', value: '×2' }],
          retreat: 1,
          regulationMark: 'G'
        },
        {
          id: 'sv7-2',
          name: 'Charizard ex',
          image: 'https://assets.pokemon.com/assets/cms2/img/cards/web/SV7/SV7_EN_2.png',
          localId: '2',
          illustrator: '5ban Graphics',
          rarity: 'Double Rare',
          category: 'Pokemon',
          set: { id: 'sv7', name: 'White Flare' },
          hp: 330,
          types: ['Fire'],
          attacks: [{ name: 'Fire Spin', damage: 230 }],
          weaknesses: [{ type: 'Water', value: '×2' }],
          retreat: 2,
          regulationMark: 'G'
        }
      ];
    }
  },

  async getSetDetails(setId: string): Promise<TCGSet> {
    try {
      const response = await apiClient.get<{ status: string; data: TCGSet }>(`/api/v1/tcgdex/sets/${setId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch set details for ${setId}:`, error);
      throw error;
    }
  }
};