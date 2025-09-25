// Common types used across the application
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

// User and Authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  plan: 'free' | 'gold' | 'platinum';
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
}

// Product types
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

// Search and filter types
export interface SearchFilters {
  query?: string;
  set?: string;
  rarity?: string;
  category?: string;
  subcategory?: string;
  pokemonType?: string;
  minPrice?: number;
  maxPrice?: number;
  condition?: string;
  sortBy?: 'name' | 'price' | 'release_date' | 'updated_at';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  size?: number;
}

// Portfolio types
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

// Alert types
export interface Alert {
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

// Form types
export interface ContactForm {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export interface NewsletterSubscription {
  email: string;
}

// Component prop types
export interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export interface InputProps {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  disabled?: boolean;
  error?: string;
  required?: boolean;
  className?: string;
}

export interface SelectProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  disabled?: boolean;
  error?: string;
  placeholder?: string;
  className?: string;
}

// Navigation types
export interface NavItem {
  name: string;
  href: string;
  icon?: string;
  description?: string;
}

export interface BreadcrumbItem {
  name: string;
  href?: string;
  current?: boolean;
}

// Modal and dialog types
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
}

// Chart and visualization types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

export interface PriceChartData {
  date: string;
  price: number;
  volume?: number;
}

// Utility types
export type Theme = 'light' | 'dark' | 'system';

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export type SortDirection = 'asc' | 'desc';

export type PlanType = 'free' | 'gold' | 'platinum';

export type CardCondition = 'mint' | 'near_mint' | 'lightly_played' | 'moderately_played' | 'heavily_played' | 'damaged';

export type PriceSource = 'tcgplayer' | 'ebay' | 'manual';

export type AlertType = 'price_target' | 'price_drop' | 'price_increase' | 'volume_spike';

// Enum-like constants
export const CARD_CONDITIONS = [
  'mint',
  'near_mint', 
  'lightly_played',
  'moderately_played',
  'heavily_played',
  'damaged'
] as const;

export const PRICE_SOURCES = [
  'tcgplayer',
  'ebay',
  'manual'
] as const;

export const ALERT_TYPES = [
  'price_target',
  'price_drop', 
  'price_increase',
  'volume_spike'
] as const;

export const PLAN_TYPES = [
  'free',
  'gold',
  'platinum'
] as const;