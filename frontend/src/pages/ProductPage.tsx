import React from 'react';
import { motion } from 'framer-motion';

const ProductPage: React.FC = () => {
  // Mock product data
  const product = {
    id: '1',
    name: 'Charizard ex',
    set: 'Base Set',
    cardNumber: '4/102',
    rarity: 'Rare Holo',
    artist: 'Mitsuhiro Arita',
    releaseDate: '1999-01-09',
    image: 'https://via.placeholder.com/400x560/ff6b6b/ffffff?text=Charizard+ex',
    description: 'A powerful Fire-type Pokémon card from the original Base Set. Highly sought after by collectors worldwide.',
    currentPrice: 1250.99,
    priceHistory: [
      { date: '2024-01-01', price: 1180.00 },
      { date: '2024-01-05', price: 1205.50 },
      { date: '2024-01-10', price: 1250.99 },
      { date: '2024-01-15', price: 1250.99 },
    ],
    marketData: {
      avgSalePrice: 1225.75,
      medianPrice: 1200.00,
      volume: 45,
      lastSale: '2024-01-14T15:30:00Z',
      volatility: 5.2,
    },
    conditions: [
      { condition: 'Mint', price: 1450.99, available: 3 },
      { condition: 'Near Mint', price: 1250.99, available: 12 },
      { condition: 'Lightly Played', price: 980.50, available: 8 },
      { condition: 'Moderately Played', price: 750.25, available: 15 },
    ],
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Product Image */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <img
              src={product.image}
              alt={product.name}
              className="w-full max-w-md mx-auto rounded-lg shadow-md"
            />
          </motion.div>

          {/* Product Details */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="space-y-6"
          >
            {/* Basic Info */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {product.name}
              </h1>
              <p className="text-lg text-gray-600 mb-4">
                {product.set} • {product.cardNumber}
              </p>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Rarity:</span>
                  <span className="ml-2 text-gray-900">{product.rarity}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Artist:</span>
                  <span className="ml-2 text-gray-900">{product.artist}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Release Date:</span>
                  <span className="ml-2 text-gray-900">{formatDate(product.releaseDate)}</span>
                </div>
              </div>

              <p className="mt-4 text-gray-600">{product.description}</p>
            </div>

            {/* Current Price */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Current Market Price
              </h2>
              <div className="text-3xl font-bold text-poke-blue mb-2">
                {formatPrice(product.currentPrice)}
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <span className="text-green-600 font-medium">↗ +2.1%</span>
                <span className="ml-2">vs last week</span>
              </div>
            </div>

            {/* Market Data */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Market Analytics
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Average Sale Price</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {formatPrice(product.marketData.avgSalePrice)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Median Price</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {formatPrice(product.marketData.medianPrice)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Monthly Volume</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {product.marketData.volume} sales
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Volatility</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {product.marketData.volatility}%
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4">
              <button className="flex-1 bg-poke-blue text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                Add to Portfolio
              </button>
              <button className="flex-1 bg-poke-yellow text-poke-blue px-6 py-3 rounded-lg font-semibold hover:bg-yellow-400 transition-colors">
                Set Price Alert
              </button>
            </div>
          </motion.div>
        </div>

        {/* Pricing by Condition */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-8 bg-white rounded-lg shadow-sm p-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Pricing by Condition
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {product.conditions.map((item) => (
              <div
                key={item.condition}
                className="border border-gray-200 rounded-lg p-4 hover:border-poke-blue transition-colors"
              >
                <div className="font-semibold text-gray-900 mb-1">
                  {item.condition}
                </div>
                <div className="text-2xl font-bold text-poke-blue mb-2">
                  {formatPrice(item.price)}
                </div>
                <div className="text-sm text-gray-600">
                  {item.available} available
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Price History Chart Placeholder */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-8 bg-white rounded-lg shadow-sm p-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Price History
          </h2>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-2">📈</div>
              <div className="text-gray-600">Price chart coming soon</div>
              <div className="text-sm text-gray-500 mt-1">
                Interactive price history with technical analysis
              </div>
            </div>
          </div>
        </motion.div>

        {/* Similar Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="mt-8 bg-white rounded-lg shadow-sm p-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Similar Cards
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="border border-gray-200 rounded-lg p-4 hover:border-poke-blue transition-colors cursor-pointer"
              >
                <div className="bg-gray-100 rounded-lg h-32 mb-3 flex items-center justify-center">
                  <span className="text-gray-400">Card {i}</span>
                </div>
                <div className="font-medium text-gray-900 mb-1">
                  Related Card {i}
                </div>
                <div className="text-sm text-gray-600 mb-2">Base Set</div>
                <div className="text-lg font-bold text-poke-blue">
                  ${(Math.random() * 1000 + 100).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ProductPage;