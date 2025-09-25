import React, { useState } from 'react';
import { motion } from 'framer-motion';

const DashboardPage: React.FC = () => {
  const [timeframe, setTimeframe] = useState('30d');

  // Mock data
  const portfolioStats = {
    totalValue: 15420.75,
    totalCards: 247,
    monthlyChange: 8.2,
    bestPerformer: 'Charizard ex - Base Set',
    bestPerformerGain: 125.50,
  };

  const recentAlerts = [
    {
      id: 1,
      card: 'Pikachu VMAX',
      type: 'Price Drop',
      change: -15.25,
      time: '2 hours ago',
    },
    {
      id: 2,
      card: 'Charizard ex',
      type: 'Price Target',
      change: 50.00,
      time: '5 hours ago',
    },
    {
      id: 3,
      card: 'Blastoise',
      type: 'Volume Spike',
      change: 0,
      time: '1 day ago',
    },
  ];

  const topHoldings = [
    {
      id: 1,
      name: 'Charizard ex',
      set: 'Base Set',
      quantity: 2,
      avgCost: 1100.00,
      currentPrice: 1250.99,
      totalValue: 2501.98,
      change: 13.7,
      image: 'https://via.placeholder.com/80x112/ff6b6b/ffffff?text=Char',
    },
    {
      id: 2,
      name: 'Pikachu VMAX',
      set: 'Vivid Voltage',
      quantity: 4,
      avgCost: 95.00,
      currentPrice: 89.99,
      totalValue: 359.96,
      change: -5.3,
      image: 'https://via.placeholder.com/80x112/feca57/ffffff?text=Pika',
    },
    {
      id: 3,
      name: 'Blastoise',
      set: 'Base Set',
      quantity: 1,
      avgCost: 400.00,
      currentPrice: 425.50,
      totalValue: 425.50,
      change: 6.4,
      image: 'https://via.placeholder.com/80x112/3742fa/ffffff?text=Blast',
    },
  ];

  const marketTrends = [
    { category: 'Vintage (1998-2003)', change: 12.5, trend: 'up' },
    { category: 'Modern (2017+)', change: -3.2, trend: 'down' },
    { category: 'WOTC Holos', change: 8.7, trend: 'up' },
    { category: 'Japanese Cards', change: 15.3, trend: 'up' },
  ];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(1)}%`;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Portfolio Dashboard
          </h1>
          <p className="text-gray-600">
            Track your Pokemon card collection performance and market insights
          </p>
        </div>

        {/* Portfolio Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(portfolioStats.totalValue)}
                </p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
            <div className="mt-2 flex items-center">
              <span className="text-green-600 text-sm font-medium">
                {formatPercentage(portfolioStats.monthlyChange)}
              </span>
              <span className="text-gray-500 text-sm ml-1">this month</span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Cards</p>
                <p className="text-2xl font-bold text-gray-900">
                  {portfolioStats.totalCards}
                </p>
              </div>
              <div className="text-3xl">🎴</div>
            </div>
            <div className="mt-2">
              <span className="text-gray-500 text-sm">Across all sets</span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Best Performer</p>
                <p className="text-lg font-bold text-gray-900 truncate">
                  {portfolioStats.bestPerformer}
                </p>
              </div>
              <div className="text-3xl">🚀</div>
            </div>
            <div className="mt-2">
              <span className="text-green-600 text-sm font-medium">
                +{formatCurrency(portfolioStats.bestPerformerGain)}
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="bg-white rounded-lg shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-gray-900">
                  {recentAlerts.length}
                </p>
              </div>
              <div className="text-3xl">🔔</div>
            </div>
            <div className="mt-2">
              <span className="text-gray-500 text-sm">Price & volume alerts</span>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Portfolio Performance Chart */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Portfolio Performance
                </h2>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue"
                >
                  <option value="7d">7 Days</option>
                  <option value="30d">30 Days</option>
                  <option value="90d">90 Days</option>
                  <option value="1y">1 Year</option>
                </select>
              </div>
              <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <div className="text-4xl mb-2">📈</div>
                  <div className="text-gray-600">Portfolio chart coming soon</div>
                  <div className="text-sm text-gray-500 mt-1">
                    Interactive performance tracking with detailed analytics
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Top Holdings */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.6 }}
              className="bg-white rounded-lg shadow-sm p-6 mt-8"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Top Holdings
              </h2>
              <div className="space-y-4">
                {topHoldings.map((holding) => (
                  <div key={holding.id} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg hover:border-poke-blue transition-colors">
                    <img
                      src={holding.image}
                      alt={holding.name}
                      className="w-16 h-20 object-cover rounded"
                    />
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{holding.name}</h3>
                      <p className="text-sm text-gray-600">{holding.set}</p>
                      <p className="text-sm text-gray-500">Qty: {holding.quantity}</p>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-gray-900">
                        {formatCurrency(holding.totalValue)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Avg: {formatCurrency(holding.avgCost)}
                      </div>
                      <div className={`text-sm font-medium ${
                        holding.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatPercentage(holding.change)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Recent Alerts */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Recent Alerts
              </h2>
              <div className="space-y-4">
                {recentAlerts.map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900 text-sm">
                        {alert.card}
                      </p>
                      <p className="text-xs text-gray-600">{alert.type}</p>
                    </div>
                    <div className="text-right">
                      {alert.change !== 0 && (
                        <p className={`text-sm font-medium ${
                          alert.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {alert.change >= 0 ? '+' : ''}{formatCurrency(alert.change)}
                        </p>
                      )}
                      <p className="text-xs text-gray-500">{alert.time}</p>
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 text-poke-blue font-medium text-sm hover:text-blue-700">
                View All Alerts →
              </button>
            </motion.div>

            {/* Market Trends */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Market Trends
              </h2>
              <div className="space-y-4">
                {marketTrends.map((trend, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {trend.category}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-medium ${
                        trend.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatPercentage(trend.change)}
                      </span>
                      <span className="text-lg">
                        {trend.trend === 'up' ? '↗️' : '↘️'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Quick Actions
              </h2>
              <div className="space-y-3">
                <button className="w-full bg-poke-blue text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm">
                  Add New Card
                </button>
                <button className="w-full bg-poke-yellow text-poke-blue px-4 py-2 rounded-lg hover:bg-yellow-400 transition-colors text-sm">
                  Create Alert
                </button>
                <button className="w-full border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm">
                  Export Portfolio
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;