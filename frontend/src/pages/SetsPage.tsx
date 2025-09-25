import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useQuery } from 'react-query';
import { tcgdexApi, TCGSet } from '../services/api';

const SetsPage: React.FC = () => {
  const [selectedEra, setSelectedEra] = useState<string>('scarlet-violet');
  const [expandedEras, setExpandedEras] = useState<Set<string>>(new Set(['scarlet-violet']));

  const eras = [
    {
      id: 'scarlet-violet',
      name: 'Scarlet & Violet',
      sets: ['sv1', 'sv2', 'sv3', 'sv4', 'sv5', 'sv6', 'sv7', 'sv8', 'sv9']
    },
    {
      id: 'sword-shield',
      name: 'Sword & Shield',
      sets: ['swsh1', 'swsh2', 'swsh3', 'swsh4', 'swsh5', 'swsh6', 'swsh7', 'swsh8', 'swsh9']
    },
    {
      id: 'sun-moon',
      name: 'Sun & Moon',
      sets: ['sm1', 'sm2', 'sm3', 'sm4', 'sm5', 'sm6', 'sm7', 'sm8', 'sm9', 'sm10', 'sm11', 'sm12']
    },
    {
      id: 'xy',
      name: 'XY',
      sets: ['xy1', 'xy2', 'xy3', 'xy4', 'xy5', 'xy6', 'xy7', 'xy8', 'xy9', 'xy10', 'xy11', 'xy12']
    },
    {
      id: 'black-white',
      name: 'Black & White',
      sets: ['bw1', 'bw2', 'bw3', 'bw4', 'bw5', 'bw6', 'bw7', 'bw8', 'bw9', 'bw10', 'bw11']
    }
  ];

  const { data: sets = [], isLoading } = useQuery(
    ['tcgdex-sets'],
    () => tcgdexApi.getSets(),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  const toggleEra = (eraId: string) => {
    const newExpanded = new Set(expandedEras);
    if (newExpanded.has(eraId)) {
      newExpanded.delete(eraId);
    } else {
      newExpanded.add(eraId);
    }
    setExpandedEras(newExpanded);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-900 to-purple-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-4">
              The Future, Your Play
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              Join today and help your child save for their story.
            </p>
            <button className="bg-poke-red hover:bg-red-700 text-white px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
              Learn More
            </button>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4 uppercase">ERA</h2>
              <div className="space-y-2">
                {eras.map((era) => (
                  <div key={era.id}>
                    <button
                      onClick={() => toggleEra(era.id)}
                      className="flex items-center w-full text-left p-2 rounded hover:bg-gray-50 transition-colors"
                    >
                      {expandedEras.has(era.id) ? (
                        <ChevronDown size={16} className="mr-2 text-gray-500" />
                      ) : (
                        <ChevronRight size={16} className="mr-2 text-gray-500" />
                      )}
                      <span className="font-medium text-gray-900">{era.name}</span>
                    </button>
                    {expandedEras.has(era.id) && (
                      <div className="ml-6 mt-1 space-y-1">
                        {era.sets.map((setId) => (
                          <button
                            key={setId}
                            onClick={() => setSelectedEra(era.id)}
                            className="block w-full text-left px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded"
                          >
                            {setId.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            <div className="mb-6 flex justify-between items-center">
              <h1 className="text-2xl font-bold text-gray-900">Sets</h1>
              <div className="flex items-center space-x-4">
                <select className="border border-gray-300 rounded px-3 py-2 text-sm">
                  <option>Sort by: Release Date</option>
                  <option>Sort by: Name</option>
                  <option>Sort by: Value</option>
                </select>
              </div>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="bg-gray-200 rounded-lg h-64 animate-pulse"></div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {sets.map((set) => (
                  <Link
                    key={set.id}
                    to={`/sets/${set.id}`}
                    className="group bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    <div className="aspect-[4/3] bg-gray-100 flex items-center justify-center p-4">
                      <img
                        src={set.logo}
                        alt={set.name}
                        className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform"
                        onError={(e) => {
                          // Create a simple SVG fallback instead of external placeholder
                          const target = e.currentTarget;
                          target.src = `data:image/svg+xml;base64,${btoa(`
                            <svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
                              <rect width="200" height="150" fill="#f3f4f6"/>
                              <text x="100" y="75" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#6b7280">
                                ${set.name}
                              </text>
                              <text x="100" y="95" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#9ca3af">
                                Set Logo
                              </text>
                            </svg>
                          `)}`;
                          target.style.opacity = '0.7';
                        }}
                      />
                    </div>
                    <div className="p-4 bg-gray-900 text-white">
                      <h3 className="font-bold text-lg mb-1">{set.name}</h3>
                      <p className="text-gray-300 text-sm">{set.series}</p>
                      <div className="flex justify-between items-center mt-2 text-sm">
                        <span>{set.totalCards} cards</span>
                        <span>{new Date(set.releaseDate).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default SetsPage;