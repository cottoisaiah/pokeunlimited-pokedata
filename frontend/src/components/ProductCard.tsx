import React from 'react';
import { motion } from 'framer-motion';
import { ProductWithPricing } from '../types';

interface ProductCardProps {
  product: ProductWithPricing;
  onClick?: () => void;
  className?: string;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, onClick, className = '' }) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const formatPercentage = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(1)}%`;
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.98 }}
      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden cursor-pointer ${className}`}
      onClick={onClick}
    >
      <div className="relative">
        <img
          src={product.product.imageUrl || `https://via.placeholder.com/200x280/e5e7eb/9ca3af?text=${encodeURIComponent(product.product.name)}`}
          alt={product.product.name}
          className="w-full h-48 object-cover"
        />
        {product.currentPrice && (
          <div className="absolute top-2 right-2 bg-white bg-opacity-90 backdrop-blur-sm px-2 py-1 rounded-md">
            <span className="text-sm font-semibold text-gray-900">
              {formatPrice(product.currentPrice)}
            </span>
          </div>
        )}
        {product.priceChangePercent !== undefined && (
          <div className={`absolute top-2 left-2 px-2 py-1 rounded-md text-xs font-medium ${
            product.priceChangePercent >= 0
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}>
            {formatPercentage(product.priceChangePercent)}
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-1 truncate">
          {product.product.name}
        </h3>
        <p className="text-sm text-gray-600 mb-2 truncate">
          {product.product.set} • {product.product.cardNumber}
        </p>
        
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500">{product.product.rarity}</span>
          {product.priceChange24h !== undefined && (
            <span className={`font-medium ${
              product.priceChange24h >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {product.priceChange24h >= 0 ? '+' : ''}
              {formatPrice(Math.abs(product.priceChange24h))}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default ProductCard;