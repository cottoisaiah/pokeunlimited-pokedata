import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronRight, ChevronLeft } from 'lucide-react';
import { useQuery } from 'react-query';
import { tcgdexApi } from '../services/api';

const SetsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedEra, setSelectedEra] = useState<string | null>(
    searchParams.get('era') || null
  );
  const [expandedEras, setExpandedEras] = useState<Set<string>>(new Set(['scarlet-violet']));
  const [selectedLang, setSelectedLang] = useState<string>(() => {
    return searchParams.get('lang') || localStorage.getItem('selected_language') || 'en';
  });
  const [currentPage, setCurrentPage] = useState<number>(() => {
    const pageParam = searchParams.get('page');
    return pageParam ? parseInt(pageParam, 10) : 1;
  });
  const ITEMS_PER_PAGE = 12;

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'de', name: 'German' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'it', name: 'Italian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'nl', name: 'Dutch' },
    { code: 'pl', name: 'Polish' },
    { code: 'pt_br', name: 'Portuguese (BR)' },
    { code: 'ru', name: 'Russian' },
    { code: 'th', name: 'Thai' },
    { code: 'zh_cn', name: 'Chinese (Simplified)' },
    { code: 'zh_tw', name: 'Chinese (Traditional)' },
    { code: 'id', name: 'Indonesian' }
  ];

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

  const { data: allSets = [], isLoading } = useQuery(
    ['tcgdex-sets', selectedLang],
    () => tcgdexApi.getSets(selectedLang),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Filter sets by selected era
  const sets = selectedEra
    ? allSets.filter(set => {
        const era = eras.find(e => e.id === selectedEra);
        return era?.sets.some(eraSetId => 
          set.id.toLowerCase().includes(eraSetId.toLowerCase())
        );
      })
    : allSets;

  // Update URL params when language, page, or era changes
  useEffect(() => {
    const params: Record<string, string> = {};
    if (selectedLang !== 'en') {
      params.lang = selectedLang;
    }
    if (currentPage > 1) {
      params.page = currentPage.toString();
    }
    if (selectedEra) {
      params.era = selectedEra;
    }
    setSearchParams(params);
    
    // Save current page to sessionStorage for back navigation
    sessionStorage.setItem('sets_page', currentPage.toString());
  }, [selectedLang, currentPage, selectedEra, setSearchParams]);

  const handleLanguageChange = (lang: string) => {
    setSelectedLang(lang);
    localStorage.setItem('selected_language', lang);
    setCurrentPage(1); // Reset to first page when changing language
  };

  const handleEraClick = (eraId: string) => {
    if (selectedEra === eraId) {
      setSelectedEra(null); // Deselect if clicking the same era
    } else {
      setSelectedEra(eraId);
    }
    setCurrentPage(1); // Reset to first page when changing era
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Calculate pagination
  const totalPages = Math.ceil(sets.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedSets = sets.slice(startIndex, endIndex);

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 7;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  const PaginationControls: React.FC<{ className?: string }> = ({ className = '' }) => (
    <div className={`flex items-center justify-center space-x-2 ${className}`}>
      <button
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft size={20} />
      </button>
      
      {getPageNumbers().map((page, index) => (
        typeof page === 'number' ? (
          <button
            key={index}
            onClick={() => handlePageChange(page)}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              currentPage === page
                ? 'bg-poke-red text-white border-poke-red'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {page}
          </button>
        ) : (
          <span key={index} className="px-2 text-gray-400">
            {page}
          </span>
        )
      ))}
      
      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronRight size={20} />
      </button>
    </div>
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
                <button
                  onClick={() => {
                    setSelectedEra(null);
                    setCurrentPage(1);
                  }}
                  className={`w-full text-left p-2 rounded transition-colors ${
                    selectedEra === null
                      ? 'bg-poke-red text-white'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <span className="font-medium">All Eras</span>
                </button>
                {eras.map((era) => (
                  <div key={era.id}>
                    <button
                      onClick={() => toggleEra(era.id)}
                      className={`flex items-center w-full text-left p-2 rounded transition-colors ${
                        selectedEra === era.id
                          ? 'bg-poke-red text-white'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      {expandedEras.has(era.id) ? (
                        <ChevronDown size={16} className="mr-2" />
                      ) : (
                        <ChevronRight size={16} className="mr-2" />
                      )}
                      <span className="font-medium">{era.name}</span>
                    </button>
                    {expandedEras.has(era.id) && (
                      <div className="ml-6 mt-1 space-y-1">
                        <button
                          onClick={() => handleEraClick(era.id)}
                          className={`block w-full text-left px-3 py-1 text-sm rounded ${
                            selectedEra === era.id
                              ? 'bg-blue-100 text-blue-900 font-medium'
                              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                          }`}
                        >
                          View All {era.name}
                        </button>
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
              <h1 className="text-2xl font-bold text-gray-900">
                Sets
                <span className="ml-3 text-base text-gray-500 font-normal">
                  ({sets.length} total)
                </span>
              </h1>
              <div className="flex items-center space-x-4">
                <select 
                  value={selectedLang}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  className="border border-gray-300 rounded px-3 py-2 text-sm"
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
                </select>
                <select className="border border-gray-300 rounded px-3 py-2 text-sm">
                  <option>Sort by: Release Date</option>
                  <option>Sort by: Name</option>
                  <option>Sort by: Value</option>
                </select>
              </div>
            </div>

            {/* Top Pagination */}
            {!isLoading && sets.length > ITEMS_PER_PAGE && (
              <div className="mb-6">
                <PaginationControls />
              </div>
            )}

            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[...Array(12)].map((_, i) => (
                  <div key={i} className="bg-gray-200 rounded-lg h-64 animate-pulse"></div>
                ))}
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                  {paginatedSets.map((set) => (
                    <Link
                      key={set.id}
                      to={`/sets/${set.id}?lang=${selectedLang}`}
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

                {/* Bottom Pagination */}
                {sets.length > ITEMS_PER_PAGE && (
                  <div className="mt-8">
                    <PaginationControls />
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default SetsPage;