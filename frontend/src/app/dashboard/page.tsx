"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Plus, TrendingDown, TrendingUp, ChevronDown, Search } from "lucide-react";
import { useGlobalData } from "@/context/GlobalDataContext";

interface Portfolio {
  id: number;
  name: string;
}

interface IndexData {
  name: string;
  price: string;
  change: string;
  percent: string;
  isUp: boolean;
  symbol?: string;
}

interface Security {
  id: number;
  symbol: string;
  name: string;
  exchange: string | null;
}

export default function Dashboard() {
  const router = useRouter();
  const { portfolios, watchlist, indices, refreshData } = useGlobalData();
  
        
  // Search State
  const [searchQuery, setSearchQuery] = useState("");
    const [isSearchFocused, setIsSearchFocused] = useState(false);

  // Direct Add State
  const [directAddSymbol, setDirectAddSymbol] = useState("");
  const [isDirectAddFocused, setIsDirectAddFocused] = useState(false);

  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [news, setNews] = useState<any[]>([]);

  
  
  
    
  const fetchNews = () => {
    api.get("/news").then(res => setNews(res.data)).catch(console.error);
  };

  useEffect(() => {
    fetchNews();
  }, []);

  const handleAddToWatchlist = async (e: React.MouseEvent, symbol: string) => {
    e.stopPropagation();
    try {
      await api.post(`/watchlist/${encodeURIComponent(symbol)}`);
      refreshData();
    } catch (err) {
      console.error("Failed to add to watchlist:", err);
      alert("Failed to add to watchlist.");
    }
  };

  // Search Logic
  const getFilteredSecurities = () => {
    if (!searchQuery.trim()) return [];
    
    const query = searchQuery.toLowerCase().trim();
    
    return allSecurities.filter(sec => {
      return sec.symbol.toLowerCase().includes(query) || sec.name.toLowerCase().includes(query);
    }).sort((a, b) => {
      const aSym = a.symbol.toLowerCase();
      const bSym = b.symbol.toLowerCase();
      const aName = a.name.toLowerCase();
      const bName = b.name.toLowerCase();
      
      if (aSym === query && bSym !== query) return -1;
      if (bSym === query && aSym !== query) return 1;
      
      if (aSym.startsWith(query) && !bSym.startsWith(query)) return -1;
      if (bSym.startsWith(query) && !aSym.startsWith(query)) return 1;
      
      if (aName.startsWith(query) && !bName.startsWith(query)) return -1;
      if (bName.startsWith(query) && !aName.startsWith(query)) return 1;
      
      return aSym.localeCompare(bSym);
    }).slice(0, 8); // Display top 8 results
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/portfolios", { name: newName, description: "" });
      setIsCreating(false);
      setNewName("");
      refreshData();
    } catch (err) {
      console.error("Failed to create portfolio");
    }
  };

  const [searchResults, setSearchResults] = useState<Security[]>([]);

  const [directAddResults, setDirectAddResults] = useState<Security[]>([]);

  
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const delayDebounceFn = setTimeout(() => {
      api.get(`/securities/search?q=${searchQuery}`).then(res => setSearchResults(res.data)).catch(console.error);
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  useEffect(() => {
    if (!directAddSymbol.trim() || directAddSymbol.length < 2) {
      setDirectAddResults([]);
      return;
    }
    const delayDebounceFn = setTimeout(() => {
      api.get(`/securities/search?q=${directAddSymbol}`).then(res => setDirectAddResults(res.data.slice(0, 5))).catch(console.error);
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [directAddSymbol]);

  const handleSelectStock = (sec: Security) => {
    setSearchQuery("");
    setIsSearchFocused(false);
    router.push(`/stocks/${sec.symbol}`);
  };

  const handleDirectAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!directAddSymbol.trim()) return;
    try {
      await api.post(`/watchlist/${encodeURIComponent(directAddSymbol.trim())}`);
      setDirectAddSymbol("");
      refreshData();
    } catch (err: any) {
      console.error("Failed to add to watchlist directly:", err);
      alert(err.response?.data?.detail || "Failed to add to watchlist. Please check the symbol and try again.");
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-8 relative">
      {isCreating && (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center">
          <div className="bg-[var(--gf-surface)] p-6 rounded-xl border border-[var(--gf-border)] w-96 shadow-2xl">
            <h3 className="font-medium mb-4 text-lg">Create Portfolio</h3>
            <form onSubmit={handleCreate} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs text-[var(--gf-gray-text)] mb-1">Portfolio Name</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2 text-sm focus:border-[var(--gf-blue)] outline-none"
                  required
                  autoFocus
                />
              </div>
              <div className="flex justify-end gap-2 mt-2">
                <button type="button" onClick={() => setIsCreating(false)} className="px-4 py-2 text-sm text-[var(--gf-gray-text)] hover:text-white transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm bg-[var(--gf-blue)] text-black font-medium rounded-lg">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sidebar - Portfolios & Navigation */}
      <div className="w-full lg:w-64 flex-shrink-0 order-last lg:order-first mb-12 lg:mb-0">
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4 cursor-pointer hover:bg-[#303134] p-2 -mx-2 rounded">
            <h3 className="font-medium text-[var(--foreground)]">Portfolios</h3>
            <ChevronDown size={16} />
          </div>
          <button onClick={() => setIsCreating(true)} className="flex items-center gap-2 text-sm bg-[var(--gf-surface)] border border-[var(--gf-border)] px-4 py-2 rounded-full hover:bg-opacity-80 transition-colors w-full justify-center">
            <Plus size={16} /> Create portfolio
          </button>
          
          <div className="mt-4 space-y-2">
            {portfolios.length === 0 ? (
              <div className="text-sm text-[var(--gf-gray-text)] text-center py-4 border border-dashed border-[var(--gf-border)] rounded-lg">No portfolios yet.</div>
            ) : (
              portfolios.map(p => (
                <Link key={p.id} href={`/portfolio/${p.id}`}>
                  <div className="text-sm text-[var(--gf-gray-text)] hover:text-[var(--foreground)] cursor-pointer py-1.5 px-2 -mx-2 rounded hover:bg-[#303134] transition-colors">{p.name}</div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Functional Auto-complete Search Bar */}
        <div className="relative mb-8 z-30">
          <div className={`bg-[var(--gf-surface)] flex items-center px-4 py-3 border border-transparent transition-all ${isSearchFocused && searchQuery.trim() ? 'rounded-t-2xl border-[var(--gf-border)] border-b-0 bg-[#303134]' : 'rounded-full hover:bg-[#303134]'}`}>
            <Search size={20} className="text-[var(--gf-gray-text)] mr-3" />
            <input 
              type="text" 
              placeholder="Search for a stock symbol or company name..." 
              className="bg-transparent border-none outline-none w-full text-[var(--foreground)]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setTimeout(() => setIsSearchFocused(false), 150)}
            />
          </div>
          
          {isSearchFocused && searchQuery.trim() && (
            <div className="absolute top-full left-0 right-0 bg-[#303134] border border-[var(--gf-border)] border-t-0 rounded-b-2xl overflow-hidden shadow-2xl max-h-[400px] overflow-y-auto">
              {searchResults.length === 0 ? (
                <div className="p-4 text-[var(--gf-gray-text)] text-sm">No stocks found matching "{searchQuery}"</div>
              ) : (
                searchResults.map(sec => (
                  <div 
                    key={sec.id}
                    className="px-6 py-3 hover:bg-[#3c4043] cursor-pointer flex justify-between items-center group"
                    onClick={() => handleSelectStock(sec)}
                  >
                    <div>
                      <div className="font-medium text-[var(--foreground)]">{sec.symbol}</div>
                      <div className="text-sm text-[var(--gf-gray-text)]">{sec.name}</div>
                    </div>
                    <button 
                      onClick={(e) => handleAddToWatchlist(e, sec.symbol)}
                      className="text-xs text-[var(--gf-blue)] opacity-0 group-hover:opacity-100 transition-opacity hover:underline"
                    >
                      Add to Watchlist
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* 1. Index Stocks (Horizontal Scroll) */}
        <div className="mb-10">
          <div className="flex gap-4 overflow-x-auto pb-4 pt-2 px-1 -mx-1 scrollbar-hide">
            {(!indices || indices.length === 0) ? (
              <>
                {[1, 2, 3, 4].map(n => (
                  <div key={n} className="min-w-[200px] h-28 bg-[var(--gf-surface)] p-4 rounded-xl border border-[var(--gf-border)] animate-pulse flex flex-col justify-between">
                    <div className="h-4 bg-[#3c4043] rounded w-1/2"></div>
                    <div className="h-6 bg-[#3c4043] rounded w-3/4"></div>
                    <div className="h-4 bg-[#3c4043] rounded w-1/3"></div>
                  </div>
                ))}
              </>
            ) : (
              indices.map((idx, i) => (
                <div key={i} onClick={() => idx.symbol && router.push(`/stocks/${idx.symbol}`)} className="min-w-[200px] bg-[var(--gf-surface)] p-4 rounded-xl border border-[var(--gf-border)] cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20 hover:bg-[#3c4043] transition-all duration-300">
                  <div className="text-sm font-medium mb-1">{idx.name}</div>
                  <div className="text-lg mb-1 tracking-tight">{idx.price}</div>
                  <div className={`text-sm flex items-center ${idx.isUp ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}`}>
                    {idx.percent} {idx.isUp ? <TrendingUp size={14} className="ml-1" /> : <TrendingDown size={14} className="ml-1" />}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 2. Watchlist */}
        <div className="mb-10">
          <h2 className="text-xl font-medium mb-4">Watchlist</h2>
          {watchlist.length === 0 ? (
            <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-12 flex flex-col items-center text-center">
              <svg className="w-24 h-24 text-[var(--gf-border)] mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <h3 className="text-lg font-medium mb-2">Track Your Favorite Stocks</h3>
              <p className="text-[var(--gf-gray-text)] mb-6 max-w-md">Your watchlist is empty. Add a stock symbol directly or search above to monitor performance.</p>
              
              <form onSubmit={handleDirectAdd} className="flex gap-2 w-full max-w-sm relative">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={directAddSymbol}
                    onChange={(e) => setDirectAddSymbol(e.target.value.toUpperCase())}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleDirectAdd(e); }}
                    onFocus={() => setIsDirectAddFocused(true)}
                    onBlur={() => setTimeout(() => setIsDirectAddFocused(false), 150)}
                    placeholder="Enter Symbol (e.g. INFY)"
                    className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-full px-4 py-2 text-sm outline-none focus:border-[var(--gf-blue)] transition-colors"
                  />
                  {isDirectAddFocused && directAddResults.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-[#303134] border border-[var(--gf-border)] rounded-xl overflow-hidden shadow-2xl z-50">
                      {directAddResults.map(sec => (
                        <div 
                          key={sec.id}
                          className="px-4 py-3 hover:bg-[#3c4043] cursor-pointer text-sm"
                          onClick={() => setDirectAddSymbol(sec.symbol)}
                        >
                          <div className="font-medium text-[var(--foreground)]">{sec.symbol}</div>
                          <div className="text-xs text-[var(--gf-gray-text)] truncate">{sec.name}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <button type="submit" className="flex items-center gap-2 text-sm bg-[var(--gf-blue)] text-black px-6 py-2 rounded-full hover:bg-opacity-90 transition-colors font-medium whitespace-nowrap">
                  <Plus size={16} /> Add
                </button>
              </form>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {watchlist.map((sec) => (
                <div key={sec.id} onClick={() => router.push(`/stocks/${sec.symbol}`)} className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-4 cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20 hover:bg-[#3c4043] transition-all duration-300 flex justify-between items-center group">
                  <div>
                    <div className="font-medium text-[var(--foreground)] tracking-tight">{sec.symbol}</div>
                    <div className="text-xs text-[var(--gf-gray-text)] truncate max-w-[150px]">{sec.name}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">View</span>
                    <ChevronDown size={16} className="-rotate-90 text-[var(--gf-gray-text)] group-hover:text-white transition-colors" />
                  </div>
                </div>
              ))}
              
              {/* Add More Card */}
              <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] border-dashed rounded-xl p-4 flex items-center justify-center relative">
                <form onSubmit={handleDirectAdd} className="flex gap-2 w-full relative">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={directAddSymbol}
                      onChange={(e) => setDirectAddSymbol(e.target.value.toUpperCase())}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleDirectAdd(e); }}
                      onFocus={() => setIsDirectAddFocused(true)}
                      onBlur={() => setTimeout(() => setIsDirectAddFocused(false), 150)}
                      placeholder="Symbol..."
                      className="w-full bg-transparent border-b border-[var(--gf-border)] px-2 py-1 text-sm outline-none focus:border-[var(--gf-blue)] transition-colors"
                    />
                    {isDirectAddFocused && directAddResults.length > 0 && (
                      <div className="absolute top-full left-0 right-0 mt-1 bg-[#303134] border border-[var(--gf-border)] rounded-lg overflow-hidden shadow-2xl z-50">
                        {directAddResults.map(sec => (
                          <div 
                            key={sec.id}
                            className="px-4 py-2 hover:bg-[#3c4043] cursor-pointer text-sm"
                            onClick={() => setDirectAddSymbol(sec.symbol)}
                          >
                            <div className="font-medium text-[var(--foreground)]">{sec.symbol}</div>
                            <div className="text-xs text-[var(--gf-gray-text)] truncate">{sec.name}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <button type="submit" className="flex items-center gap-1 text-sm bg-[var(--gf-blue)] text-black px-3 py-1 rounded hover:bg-opacity-90 transition-colors font-medium whitespace-nowrap">
                    <Plus size={14} /> Add
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>

        {/* 3. Finance Related News */}
        <div className="mb-10">
          <h2 className="text-xl font-medium mb-4">India market summary</h2>
          <div className="space-y-4">
            {news.length === 0 ? (
              <>
                {[1, 2, 3].map(n => (
                  <div key={n} className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-5 flex justify-between items-center animate-pulse">
                    <div className="flex gap-4 items-center w-full">
                      <div className="w-16 h-16 bg-[#3c4043] rounded flex-shrink-0"></div>
                      <div className="flex flex-col gap-2 w-full max-w-xl">
                        <div className="h-5 bg-[#3c4043] rounded w-full"></div>
                        <div className="h-3 bg-[#3c4043] rounded w-1/3 mt-1"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              news.slice(0, 5).map((n, i) => (
                <a key={i} href={n.link} target="_blank" rel="noopener noreferrer" className="block bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-5 hover:bg-[#3c4043] transition-colors flex justify-between items-center">
                  <div className="flex gap-4 items-center">
                    {n.thumbnail && (
                      <img src={n.thumbnail} alt={n.title} className="w-16 h-16 object-cover rounded" />
                    )}
                    <div>
                      <h3 className="font-medium text-[var(--foreground)] mb-1 line-clamp-2">{n.title}</h3>
                      <span className="text-xs text-[var(--gf-gray-text)]">{n.publisher} • {new Date(n.publishedAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <ChevronDown size={20} className="-rotate-90 text-[var(--gf-gray-text)]" />
                </a>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
