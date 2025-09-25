import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SearchResult {
  id: string;
  name: string;
  set: string;
  rarity: string;
  price: number;
  image: string;
  condition: string;
  lastUpdated: string;
}

const SearchPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    set: '',
    rarity: '',
    condition: '',
    priceMin: '',
    priceMax: '',
  });
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState('name');

  // Mock data for demonstration
  const mockResults: SearchResult[] = [
    {
      id: '1',
      name: 'Charizard ex',
      set: 'Base Set',
      rarity: 'Rare Holo',
      price: 1250.99,
      image: 'https://via.placeholder.com/200x280/ff6b6b/ffffff?text=Charizard',
      condition: 'Near Mint',
      lastUpdated: '2024-01-15T10:30:00Z',
    },
    {
      id: '2',
      name: 'Pikachu VMAX',
      set: 'Vivid Voltage',
      rarity: 'Rainbow Rare',
      price: 89.99,
      image: 'https://via.placeholder.com/200x280/feca57/ffffff?text=Pikachu',
      condition: 'Mint',
      lastUpdated: '2024-01-15T09:15:00Z',
    },
    {
      id: '3',
      name: 'Blastoise',
      set: 'Base Set',
      rarity: 'Rare Holo',
      price: 425.50,
      image: 'https://via.placeholder.com/200x280/3742fa/ffffff?text=Blastoise',
      condition: 'Lightly Played',
      lastUpdated: '2024-01-15T08:45:00Z',
    },
    {
      id: '4',
      name: 'Venusaur',
      set: 'Base Set',
      rarity: 'Rare Holo',
      price: 315.75,
      image: 'https://via.placeholder.com/200x280/2ed573/ffffff?text=Venusaur',
      condition: 'Near Mint',
      lastUpdated: '2024-01-15T11:20:00Z',
    },
  ];

  const sets = ['All Sets', 'Base Set', 'Jungle', 'Fossil', 'Team Rocket', 'Vivid Voltage', 'Battle Styles'];
  const rarities = ['All Rarities', 'Common', 'Uncommon', 'Rare', 'Rare Holo', 'Rainbow Rare', 'Secret Rare'];
  const conditions = ['All Conditions', 'Mint', 'Near Mint', 'Lightly Played', 'Moderately Played', 'Heavily Played'];

  useEffect(() => {
    if (searchQuery.trim() || Object.values(filters).some(f => f)) {
      setLoading(true);
      // Simulate API call
      setTimeout(() => {
        setResults(mockResults);
        setLoading(false);
      }, 1000);
    } else {
      setResults([]);
    }
  }, [searchQuery, filters]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search logic would go here
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const formatLastUpdated = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Search Pokemon Cards
          </h1>
          <p className="text-gray-600">
            Find and analyze pricing data for over 50,000 Pokemon cards
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-6 gap-4">
            {/* Search Input */}
            <div className="lg:col-span-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                Card Name
              </label>
              <input
                type="text"
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g., Charizard, Pikachu VMAX..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              />
            </div>

            {/* Set Filter */}
            <div>
              <label htmlFor="set" className="block text-sm font-medium text-gray-700 mb-1">
                Set
              </label>
              <select
                id="set"
                value={filters.set}
                onChange={(e) => setFilters({ ...filters, set: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              >
                {sets.map(set => (
                  <option key={set} value={set === 'All Sets' ? '' : set}>
                    {set}
                  </option>
                ))}
              </select>
            </div>

            {/* Rarity Filter */}
            <div>
              <label htmlFor="rarity" className="block text-sm font-medium text-gray-700 mb-1">
                Rarity
              </label>
              <select
                id="rarity"
                value={filters.rarity}
                onChange={(e) => setFilters({ ...filters, rarity: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              >
                {rarities.map(rarity => (
                  <option key={rarity} value={rarity === 'All Rarities' ? '' : rarity}>
                    {rarity}
                  </option>
                ))}
              </select>
            </div>

            {/* Condition Filter */}
            <div>
              <label htmlFor="condition" className="block text-sm font-medium text-gray-700 mb-1">
                Condition
              </label>
              <select
                id="condition"
                value={filters.condition}
                onChange={(e) => setFilters({ ...filters, condition: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              >
                {conditions.map(condition => (
                  <option key={condition} value={condition === 'All Conditions' ? '' : condition}>
                    {condition}
                  </option>
                ))}
              </select>
            </div>

            {/* Search Button */}
            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-poke-blue text-white px-6 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-poke-blue focus:ring-offset-2 transition-colors disabled:opacity-50"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>

          {/* Price Range */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md">
            <div>
              <label htmlFor="priceMin" className="block text-sm font-medium text-gray-700 mb-1">
                Min Price
              </label>
              <input
                type="number"
                id="priceMin"
                value={filters.priceMin}
                onChange={(e) => setFilters({ ...filters, priceMin: e.target.value })}
                placeholder="$0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              />
            </div>
            <div>
              <label htmlFor="priceMax" className="block text-sm font-medium text-gray-700 mb-1">
                Max Price
              </label>
              <input
                type="number"
                id="priceMax"
                value={filters.priceMax}
                onChange={(e) => setFilters({ ...filters, priceMax: e.target.value })}
                placeholder="$∞"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              />
            </div>
          </div>
        </form>

        {/* Results Header */}
        {results.length > 0 && (
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {results.length} Results Found
              </h2>
              <p className="text-gray-600">
                Showing cards matching your search criteria
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <label htmlFor="sort" className="text-sm font-medium text-gray-700">
                Sort by:
              </label>
              <select
                id="sort"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-poke-blue focus:border-transparent"
              >
                <option value="name">Name</option>
                <option value="price-high">Price: High to Low</option>
                <option value="price-low">Price: Low to High</option>
                <option value="updated">Recently Updated</option>
              </select>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-poke-blue"></div>
          </div>
        )}

        {/* Results Grid */}
        <AnimatePresence>
          {results.length > 0 && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            >
              {results.map((card, index) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden group cursor-pointer"
                >
                  <div className="relative">
                    <img
                      src={card.image}
                      alt={card.name}
                      className="w-full h-64 object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-2 right-2 bg-white bg-opacity-90 px-2 py-1 rounded-md">
                      <span className="text-sm font-semibold text-gray-900">
                        {formatPrice(card.price)}
                      </span>
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-poke-blue transition-colors">
                      {card.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">{card.set}</p>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-500">{card.rarity}</span>
                      <span className="text-gray-500">{card.condition}</span>
                    </div>
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-400">
                        Updated: {formatLastUpdated(card.lastUpdated)}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!loading && results.length === 0 && (searchQuery || Object.values(filters).some(f => f)) && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No cards found
            </h3>
            <p className="text-gray-600 mb-4">
              Try adjusting your search criteria or browse popular cards
            </p>
            <button className="bg-poke-blue text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors">
              Clear Filters
            </button>
          </div>
        )}

        {/* Initial State */}
        {!loading && results.length === 0 && !searchQuery && !Object.values(filters).some(f => f) && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Start Your Search
            </h3>
            <p className="text-gray-600">
              Enter a card name or use filters to find Pokemon cards
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;