import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  portfolioService,
  PortfolioFilters,
  AddToPortfolioRequest,
  UpdatePortfolioItemRequest,
  CreateAlertRequest
} from '../services/portfolio';

// Query keys for React Query caching
export const PORTFOLIO_QUERY_KEYS = {
  all: ['portfolio'] as const,
  items: (filters: PortfolioFilters) => [...PORTFOLIO_QUERY_KEYS.all, 'items', filters] as const,
  summary: () => [...PORTFOLIO_QUERY_KEYS.all, 'summary'] as const,
  performance: (days: number) => [...PORTFOLIO_QUERY_KEYS.all, 'performance', days] as const,
  item: (id: string) => [...PORTFOLIO_QUERY_KEYS.all, 'item', id] as const,
  analytics: (timeframe: string) => [...PORTFOLIO_QUERY_KEYS.all, 'analytics', timeframe] as const,
  bySet: () => [...PORTFOLIO_QUERY_KEYS.all, 'bySet'] as const,
  byRarity: () => [...PORTFOLIO_QUERY_KEYS.all, 'byRarity'] as const,
  byCondition: () => [...PORTFOLIO_QUERY_KEYS.all, 'byCondition'] as const,
  alerts: () => [...PORTFOLIO_QUERY_KEYS.all, 'alerts'] as const,
};

// Hook for getting portfolio items
export const usePortfolio = (filters: PortfolioFilters = {}) => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.items(filters),
    queryFn: () => portfolioService.getPortfolio(filters),
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Hook for getting portfolio summary
export const usePortfolioSummary = () => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.summary(),
    queryFn: () => portfolioService.getPortfolioSummary(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Hook for getting portfolio performance
export const usePortfolioPerformance = (days: number = 30) => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.performance(days),
    queryFn: () => portfolioService.getPortfolioPerformance(days),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook for getting a single portfolio item
export const usePortfolioItem = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.item(id),
    queryFn: () => portfolioService.getPortfolioItem(id),
    enabled: enabled && !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook for portfolio analytics
export const usePortfolioAnalytics = (timeframe: '7d' | '30d' | '90d' | '1y' = '30d') => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.analytics(timeframe),
    queryFn: () => portfolioService.getPortfolioAnalytics(timeframe),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Hook for portfolio breakdown by set
export const usePortfolioBySet = () => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.bySet(),
    queryFn: () => portfolioService.getPortfolioBySet(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Hook for portfolio breakdown by rarity
export const usePortfolioByRarity = () => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.byRarity(),
    queryFn: () => portfolioService.getPortfolioByRarity(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Hook for portfolio breakdown by condition
export const usePortfolioByCondition = () => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.byCondition(),
    queryFn: () => portfolioService.getPortfolioByCondition(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Hook for portfolio alerts
export const usePortfolioAlerts = () => {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.alerts(),
    queryFn: () => portfolioService.getPortfolioAlerts(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Mutation hooks
export const useAddToPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (item: AddToPortfolioRequest) => portfolioService.addToPortfolio(item),
    onSuccess: () => {
      // Invalidate portfolio-related queries
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

export const useUpdatePortfolioItem = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: UpdatePortfolioItemRequest }) =>
      portfolioService.updatePortfolioItem(id, updates),
    onSuccess: (_, variables) => {
      // Invalidate specific item and summary
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.item(variables.id));
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.summary());
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

export const useRemoveFromPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => portfolioService.removeFromPortfolio(id),
    onSuccess: () => {
      // Invalidate all portfolio queries
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

export const useBulkAddToPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (items: AddToPortfolioRequest[]) => portfolioService.bulkAddToPortfolio(items),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

export const useBulkUpdatePortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (updates: Array<{ id: string; updates: UpdatePortfolioItemRequest }>) =>
      portfolioService.bulkUpdatePortfolio(updates),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

export const useBulkDeleteFromPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (ids: string[]) => portfolioService.bulkDeleteFromPortfolio(ids),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

// Alert mutations
export const useCreatePortfolioAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (alert: CreateAlertRequest) => portfolioService.createPortfolioAlert(alert),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.alerts());
    },
  });
};

export const useUpdatePortfolioAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CreateAlertRequest> }) =>
      portfolioService.updatePortfolioAlert(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.alerts());
    },
  });
};

export const useDeletePortfolioAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => portfolioService.deletePortfolioAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.alerts());
    },
  });
};

export const useTogglePortfolioAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => portfolioService.togglePortfolioAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.alerts());
    },
  });
};

// Import/Export mutations
export const useImportPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => portfolioService.importPortfolio(file),
    onSuccess: () => {
      queryClient.invalidateQueries(PORTFOLIO_QUERY_KEYS.all);
    },
  });
};

export const useExportPortfolio = () => {
  return useMutation({
    mutationFn: (format: 'csv' | 'json' = 'csv') => portfolioService.exportPortfolio(format),
    onSuccess: (blob, format) => {
      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `portfolio-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
  });
};

// Sharing mutations
export const useSharePortfolio = () => {
  return useMutation({
    mutationFn: (isPublic: boolean) => portfolioService.sharePortfolio(isPublic),
  });
};

export const useSharedPortfolio = (shareId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['sharedPortfolio', shareId],
    queryFn: () => portfolioService.getSharedPortfolio(shareId),
    enabled: enabled && !!shareId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};