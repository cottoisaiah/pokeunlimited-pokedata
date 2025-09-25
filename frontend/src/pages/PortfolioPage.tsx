import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface PortfolioCard {
  id: string;
  name: string;
  set: string;
  rarity: string;
  condition: string;
  quantity: number;
  purchasePrice: number;
  currentPrice: number;
  purchaseDate: string;
  image: string;
}

const PortfolioPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('value');
  const [filterBy, setFilterBy] = useState('all');

  // Mock portfolio data
  const portfolioCards: PortfolioCard[] = [
    {
      id: '1',
      name: 'Charizard ex',
      set: 'Base Set',
      rarity: 'Rare Holo',
      condition: 'Near Mint',
      quantity: 1,
      purchasePrice: 1100.00,
      currentPrice: 1250.99,
      purchaseDate: '2024-01-01',
      image: 'https://via.placeholder.com/200x280/ff6b6b/ffffff?text=Charizard',
    },
    {
      id: '2',
      name: 'Blastoise',
      set: 'Base Set',
      rarity: 'Rare Holo',
      condition: 'Lightly Played',
      quantity: 1,
      purchasePrice: 400.00,
      currentPrice: 425.50,
      purchaseDate: '2024-01-05',
      image: 'https://via.placeholder.com/200x280/3742fa/ffffff?text=Blastoise',
    },
    {
      id: '3',
      name: 'Venusaur',
      set: 'Base Set',
      rarity: 'Rare Holo',
      condition: 'Near Mint',
      quantity: 2,
      purchasePrice: 280.00,
      currentPrice: 315.75,
      purchaseDate: '2024-01-10',
      image: 'https://via.placeholder.com/200x280/2ed573/ffffff?text=Venusaur',
    },
    {
      id: '4',
      name: 'Pikachu VMAX',
      set: 'Vivid Voltage',
      rarity: 'Rainbow Rare',
      condition: 'Mint',
      quantity: 3,
      purchasePrice: 75.00,
      currentPrice: 89.99,
      purchaseDate: '2024-01-12',
      image: 'https://via.placeholder.com/200x280/feca57/ffffff?text=Pikachu',
    },
  ];

  // Calculate portfolio statistics
  const portfolioStats = {
    totalValue: portfolioCards.reduce((sum, card) => sum + (card.currentPrice * card.quantity), 0),
    totalCost: portfolioCards.reduce((sum, card) => sum + (card.purchasePrice * card.quantity), 0),
    totalCards: portfolioCards.reduce((sum, card) => sum + card.quantity, 0),
    uniqueCards: portfolioCards.length,
  };

  const totalGainLoss = portfolioStats.totalValue - portfolioStats.totalCost;
  const gainLossPercentage = ((totalGainLoss / portfolioStats.totalCost) * 100);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getGainLossColor = (current: number, purchase: number) => {
    const diff = current - purchase;
    return diff >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getGainLossValue = (current: number, purchase: number, quantity: number) => {
    const diff = (current - purchase) * quantity;
    const percentage = ((diff / (purchase * quantity)) * 100);
    return {
      value: diff,
      percentage: percentage,
      formatted: `${diff >= 0 ? '+' : ''}${formatPrice(diff)} (${diff >= 0 ? '+' : ''}${percentage.toFixed(1)}%)`
    };
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold text-gray-900 mb-2"
          >
            My Portfolio
          </motion.h1>
          <p className="text-gray-600">
            Track and manage your Pokemon card collection
          </p>
        </div>

        {/* Portfolio Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="text-sm font-medium text-gray-600 mb-1">Total Value</div>
            <div className="text-2xl font-bold text-gray-900">{formatPrice(portfolioStats.totalValue)}</div>
            <div className={`text-sm font-medium ${totalGainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {totalGainLoss >= 0 ? '+' : ''}{formatPrice(totalGainLoss)} ({gainLossPercentage >= 0 ? '+' : ''}{gainLossPercentage.toFixed(1)}%)
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="text-sm font-medium text-gray-600 mb-1">Total Cost</div>
            <div className="text-2xl font-bold text-gray-900">{formatPrice(portfolioStats.totalCost)}</div>
            <div className="text-sm text-gray-500">Initial investment</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="text-sm font-medium text-gray-600 mb-1">Total Cards</div>
            <div className="text-2xl font-bold text-gray-900">{portfolioStats.totalCards}</div>
            <div className="text-sm text-gray-500">{portfolioStats.uniqueCards} unique cards</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="text-sm font-medium text-gray-600 mb-1">Best Performer</div>
            <div className="text-lg font-bold text-gray-900">Charizard ex</div>
            <div className="text-sm text-green-600">+13.7% gain</div>
          </motion.div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">View:</label>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'grid' 
                      ? 'bg-poke-blue text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Grid
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'list' 
                      ? 'bg-poke-blue text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  List
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <label htmlFor="sort" className="text-sm font-medium text-gray-700">Sort by:</label>
                <select
                  id="sort"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
                >
                  <option value="value">Current Value</option>
                  <option value="gain">Gain/Loss</option>
                  <option value="name">Name</option>
                  <option value="date">Purchase Date</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <button className="bg-poke-yellow text-poke-blue px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-400 transition-colors">
                Add Card
              </button>
              <button className="bg-poke-blue text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                Export Portfolio
              </button>
            </div>
          </div>
        </div>

        {/* Portfolio Grid/List View */}
        <AnimatePresence mode="wait">
          {viewMode === 'grid' ? (
            <motion.div
              key="grid"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            >
              {portfolioCards.map((card, index) => {
                const gainLoss = getGainLossValue(card.currentPrice, card.purchasePrice, card.quantity);
                return (
                  <motion.div
                    key={card.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden"
                  >
                    <div className="relative">
                      <img
                        src={card.image}
                        alt={card.name}
                        className="w-full h-48 object-cover"
                      />
                      <div className="absolute top-2 right-2 bg-white bg-opacity-90 px-2 py-1 rounded-md">
                        <span className="text-xs font-semibold text-gray-900">
                          Qty: {card.quantity}
                        </span>
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 mb-1">{card.name}</h3>
                      <p className="text-sm text-gray-600 mb-2">{card.set} • {card.condition}</p>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Current:</span>
                          <span className="font-medium">{formatPrice(card.currentPrice * card.quantity)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Cost:</span>
                          <span>{formatPrice(card.purchasePrice * card.quantity)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Gain/Loss:</span>
                          <span className={getGainLossColor(card.currentPrice, card.purchasePrice)}>
                            {gainLoss.formatted}
                          </span>
                        </div>
                      </div>
                      
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-400">
                          Purchased: {formatDate(card.purchaseDate)}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          ) : (
            <motion.div
              key="list"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-lg shadow-sm overflow-hidden"
            >
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Card</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Set</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Condition</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Qty</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Current Value</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Gain/Loss</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolioCards.map((card) => {
                      const gainLoss = getGainLossValue(card.currentPrice, card.purchasePrice, card.quantity);
                      return (
                        <tr key={card.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-4 px-4">
                            <div className="flex items-center space-x-3">
                              <img
                                src={card.image}
                                alt={card.name}
                                className="w-12 h-16 object-cover rounded"
                              />
                              <div>
                                <div className="font-medium text-gray-900">{card.name}</div>
                                <div className="text-sm text-gray-500">{card.rarity}</div>
                              </div>
                            </div>
                          </td>
                          <td className="py-4 px-4 text-sm text-gray-900">{card.set}</td>
                          <td className="py-4 px-4 text-sm text-gray-900">{card.condition}</td>
                          <td className="py-4 px-4 text-sm text-gray-900">{card.quantity}</td>
                          <td className="py-4 px-4 text-sm text-gray-900">
                            {formatPrice(card.purchasePrice * card.quantity)}
                          </td>
                          <td className="py-4 px-4 text-sm font-medium text-gray-900">
                            {formatPrice(card.currentPrice * card.quantity)}
                          </td>
                          <td className="py-4 px-4 text-sm">
                            <span className={getGainLossColor(card.currentPrice, card.purchasePrice)}>
                              {gainLoss.formatted}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-sm">
                            <button className="text-poke-blue hover:text-blue-700 font-medium mr-3">
                              Edit
                            </button>
                            <button className="text-red-600 hover:text-red-700 font-medium">
                              Remove
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default PortfolioPage;