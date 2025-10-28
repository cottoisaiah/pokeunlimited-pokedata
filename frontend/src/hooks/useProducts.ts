import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  productsService, 
  ProductSearchParams
} from '../services/products';

// Query keys for React Query caching
export const PRODUCTS_QUERY_KEYS = {
  all: ['products'] as const,
  search: (params: ProductSearchParams) => [...PRODUCTS_QUERY_KEYS.all, 'search', params] as const,
  detail: (id: string) => [...PRODUCTS_QUERY_KEYS.all, 'detail', id] as const,
  priceHistory: (id: string, days: number, condition?: string) => 
    [...PRODUCTS_QUERY_KEYS.all, 'priceHistory', id, days, condition] as const,
  marketAnalysis: (id: string) => [...PRODUCTS_QUERY_KEYS.all, 'marketAnalysis', id] as const,
  similar: (id: string) => [...PRODUCTS_QUERY_KEYS.all, 'similar', id] as const,
  featured: () => [...PRODUCTS_QUERY_KEYS.all, 'featured'] as const,
  trending: () => [...PRODUCTS_QUERY_KEYS.all, 'trending'] as const,
  sets: () => [...PRODUCTS_QUERY_KEYS.all, 'sets'] as const,
  rarities: () => [...PRODUCTS_QUERY_KEYS.all, 'rarities'] as const,
  categories: () => [...PRODUCTS_QUERY_KEYS.all, 'categories'] as const,
};

// Hook for searching products
export const useProductSearch = (params: ProductSearchParams, enabled: boolean = true) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.search(params),
    queryFn: () => productsService.searchProducts(params),
    enabled,
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Hook for getting a single product
export const useProduct = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.detail(id),
    queryFn: () => productsService.getProduct(id),
    enabled: enabled && !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook for getting product price history
export const useProductPriceHistory = (
  id: string, 
  days: number = 30, 
  condition?: string,
  enabled: boolean = true
) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.priceHistory(id, days, condition),
    queryFn: () => productsService.getProductPriceHistory(id, days, condition),
    enabled: enabled && !!id,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Hook for getting product market analysis
export const useProductMarketAnalysis = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.marketAnalysis(id),
    queryFn: () => productsService.getProductMarketAnalysis(id),
    enabled: enabled && !!id,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Hook for getting similar products
export const useSimilarProducts = (id: string, limit: number = 8, enabled: boolean = true) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.similar(id),
    queryFn: () => productsService.getSimilarProducts(id, limit),
    enabled: enabled && !!id,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
};

// Hook for getting featured products
export const useFeaturedProducts = (limit: number = 12) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.featured(),
    queryFn: () => productsService.getFeaturedProducts(limit),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Hook for getting trending products
export const useTrendingProducts = (limit: number = 12) => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.trending(),
    queryFn: () => productsService.getTrendingProducts(limit),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Hook for getting available sets
export const useAvailableSets = () => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.sets(),
    queryFn: () => productsService.getAvailableSets(),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
};

// Hook for getting available rarities
export const useAvailableRarities = () => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.rarities(),
    queryFn: () => productsService.getAvailableRarities(),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
};

// Hook for getting available categories
export const useAvailableCategories = () => {
  return useQuery({
    queryKey: PRODUCTS_QUERY_KEYS.categories(),
    queryFn: () => productsService.getAvailableCategories(),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
};

// Mutation hooks for external searches (Premium features)
export const useTCGPlayerSearch = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ query, exact }: { query: string; exact?: boolean }) =>
      productsService.searchTCGPlayer(query, exact),
    onSuccess: () => {
      // Optionally invalidate related queries
      queryClient.invalidateQueries(PRODUCTS_QUERY_KEYS.all);
    },
  });
};

export const useEbaySearch = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ query, condition }: { query: string; condition?: string }) =>
      productsService.searchEbay(query, condition),
    onSuccess: () => {
      // Optionally invalidate related queries
      queryClient.invalidateQueries(PRODUCTS_QUERY_KEYS.all);
    },
  });
};

// Mutation for bulk price checking (Platinum feature)
export const useBulkPriceCheck = () => {
  return useMutation({
    mutationFn: (productIds: string[]) => productsService.bulkPriceCheck(productIds),
  });
};

// Mutation for exporting product data
export const useExportProducts = () => {
  return useMutation({
    mutationFn: (params: ProductSearchParams) => productsService.exportProductData(params),
    onSuccess: (blob) => {
      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `products-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
  });
};