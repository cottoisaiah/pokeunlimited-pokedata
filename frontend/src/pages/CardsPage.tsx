import React, { useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Search, Plus } from 'lucide-react';
import { useQuery } from 'react-query';
import { tcgdexApi } from '../services/api';

const CardsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const lang = queryParams.get('lang') || localStorage.getItem('selected_language') || 'en';
  
  // Preserve the page and lang params for the back link
  const backToSetsUrl = `/sets?${new URLSearchParams({
    ...(lang !== 'en' ? { lang } : {}),
    ...(sessionStorage.getItem('sets_page') ? { page: sessionStorage.getItem('sets_page')! } : {})
  }).toString()}`;
  
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('number');

  const { data: cards = [], isLoading } = useQuery(
    ['tcgdex-cards', id, lang],
    () => id ? tcgdexApi.getSetCards(id, lang) : Promise.resolve([]),
    {
      enabled: !!id,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  const { data: setInfo } = useQuery(
    ['tcgdex-set', id, lang],
    () => id ? tcgdexApi.getSetDetails(id, lang) : Promise.resolve(null),
    {
      enabled: !!id,
      staleTime: 10 * 60 * 1000, // 10 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
    }
  );

  const filteredCards = cards.filter(card =>
    card.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    card.localId.includes(searchTerm)
  );

  const sortedCards = [...filteredCards].sort((a, b) => {
    switch (sortBy) {
      case 'number':
        return (a.localId || '').localeCompare(b.localId || '');
      case 'name':
        return a.name.localeCompare(b.name);
      case 'price-high':
        return (b.price || 0) - (a.price || 0);
      case 'price-low':
        return (a.price || 0) - (b.price || 0);
      default:
        return 0;
    }
  });

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <nav className="text-sm text-gray-500 mb-4">
            <Link to="/" className="hover:text-gray-700">Home</Link>
            <span className="mx-2">{'>'}</span>
            <Link to={backToSetsUrl} className="hover:text-gray-700">Sets</Link>
            <span className="mx-2">{'>'}</span>
            <span className="text-gray-900">{setInfo?.name || 'Loading...'}</span>
          </nav>

          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{setInfo?.name || 'Loading...'}</h1>
              <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600">
                <span>{setInfo?.series || 'Loading...'}</span>
                <span>{setInfo?.totalCards || 0} cards</span>
                <span>Released {setInfo?.releaseDate ? new Date(setInfo.releaseDate).toLocaleDateString() : 'Loading...'}</span>
              </div>
            </div>

            <div className="mt-4 lg:mt-0">
              <button className="bg-poke-red hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors">
                Add to Portfolio
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-gray-50 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search cards..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-poke-red focus:border-transparent"
                />
              </div>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2 text-sm"
              >
                <option value="number">Sort by: Number</option>
                <option value="name">Sort by: Name</option>
                <option value="price-high">Price: High to Low</option>
                <option value="price-low">Price: Low to High</option>
              </select>
            </div>

            <div className="text-sm text-gray-600">
              Showing {sortedCards.length} of {cards.length} cards
            </div>
          </div>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {[...Array(20)].map((_, i) => (
              <div key={i} className="bg-gray-200 rounded-lg h-80 animate-pulse"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {sortedCards.map((card) => (
              <div
                key={card.id}
                className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow group"
              >
                <div className="aspect-[3/4] bg-gray-50 flex items-center justify-center p-4">
                  <img
                    src={card.image}
                    alt={card.name}
                    className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform"
                    onError={(e) => {
                      // Create a simple SVG fallback instead of external placeholder
                      const target = e.currentTarget;
                      target.src = `data:image/svg+xml;base64,${btoa(`
                        <svg width="200" height="280" xmlns="http://www.w3.org/2000/svg">
                          <rect width="200" height="280" fill="#f9fafb"/>
                          <rect x="20" y="20" width="160" height="240" fill="#e5e7eb" rx="8"/>
                          <text x="100" y="140" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#6b7280">
                            ${card.name}
                          </text>
                          <text x="100" y="160" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#9ca3af">
                            Card Image
                          </text>
                        </svg>
                      `)}`;
                      target.style.opacity = '0.7';
                    }}
                  />
                </div>

                <div className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm mb-1">{card.name}</h3>
                      <p className="text-xs text-gray-500">{card.localId}</p>
                    </div>
                    <button className="w-8 h-8 bg-blue-100 hover:bg-blue-200 rounded-full flex items-center justify-center transition-colors">
                      <Plus size={16} className="text-blue-600" />
                    </button>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-900">${(card.price || 0).toFixed(2)}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      card.rarity === 'Common' ? 'bg-gray-100 text-gray-700' :
                      card.rarity === 'Uncommon' ? 'bg-blue-100 text-blue-700' :
                      card.rarity === 'Rare' ? 'bg-purple-100 text-purple-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {card.rarity}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CardsPage;