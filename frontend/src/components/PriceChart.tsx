import React from 'react';
import { PriceChartData } from '../types';

interface PriceChartProps {
  data: PriceChartData[];
  title?: string;
  height?: number;
  className?: string;
}

const PriceChart: React.FC<PriceChartProps> = ({
  data,
  title = 'Price History',
  height = 300,
  className = '',
}) => {
  // This is a placeholder for the actual chart implementation
  // In a real application, you would use a charting library like Recharts, Chart.js, or D3.js

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const latestPrice = data[data.length - 1]?.price || 0;
  const earliestPrice = data[0]?.price || 0;
  const priceChange = latestPrice - earliestPrice;
  const priceChangePercent = earliestPrice ? (priceChange / earliestPrice) * 100 : 0;

  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 ${className}`}>
      {/* Chart Header */}
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            {formatPrice(latestPrice)}
          </div>
          <div className={`text-sm font-medium ${
            priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {priceChangePercent >= 0 ? '+' : ''}
            {formatPrice(Math.abs(priceChange))} ({priceChangePercent.toFixed(1)}%)
          </div>
        </div>
      </div>

      {/* Chart Placeholder */}
      <div 
        className="relative bg-gray-50 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300"
        style={{ height: `${height}px` }}
      >
        <div className="text-center">
          <div className="text-4xl mb-2">📈</div>
          <div className="text-gray-600 font-medium">Interactive Price Chart</div>
          <div className="text-sm text-gray-500 mt-1">
            Chart implementation coming soon
          </div>
          <div className="text-xs text-gray-400 mt-2">
            {data.length} data points • {data.length > 0 ? `${data[0].date} to ${data[data.length - 1].date}` : 'No data'}
          </div>
        </div>

        {/* Simple visualization overlay */}
        {data.length > 1 && (
          <div className="absolute inset-4 flex items-end justify-between opacity-20">
            {data.slice(0, 10).map((point, index) => {
              const maxPrice = Math.max(...data.map(d => d.price));
              const minPrice = Math.min(...data.map(d => d.price));
              const range = maxPrice - minPrice;
              const normalizedHeight = range > 0 ? ((point.price - minPrice) / range) * 100 : 50;
              
              return (
                <div
                  key={index}
                  className="bg-poke-blue rounded-t"
                  style={{
                    height: `${Math.max(normalizedHeight, 5)}%`,
                    width: `${Math.max(80 / data.length, 2)}%`,
                  }}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* Data Summary */}
      {data.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div className="text-center">
            <div className="text-sm text-gray-600">Highest</div>
            <div className="font-semibold text-gray-900">
              {formatPrice(Math.max(...data.map(d => d.price)))}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600">Lowest</div>
            <div className="font-semibold text-gray-900">
              {formatPrice(Math.min(...data.map(d => d.price)))}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600">Average</div>
            <div className="font-semibold text-gray-900">
              {formatPrice(data.reduce((sum, d) => sum + d.price, 0) / data.length)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600">Data Points</div>
            <div className="font-semibold text-gray-900">
              {data.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PriceChart;