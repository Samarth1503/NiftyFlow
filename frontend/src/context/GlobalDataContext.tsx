"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from './AuthContext';

interface Portfolio {
  id: number;
  name: string;
  total_value?: number;
}

interface WatchlistSecurity {
  id: number;
  symbol: string;
  name: string;
  current_price?: number;
}

interface IndexData {
  id: string;
  name: string;
  symbol?: string;
  value: number;
  change: number;
  changePercent: number;
}

interface GlobalDataContextType {
  portfolios: Portfolio[];
  watchlist: WatchlistSecurity[];
  indices: IndexData[];
  refreshData: () => Promise<void>;
  isFetching: boolean;
}

const GlobalDataContext = createContext<GlobalDataContextType>({
  portfolios: [],
  watchlist: [],
  indices: [],
  refreshData: async () => {},
  isFetching: false,
});

export const GlobalDataProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistSecurity[]>([]);
  const [indices, setIndices] = useState<IndexData[]>([]);
  const [isFetching, setIsFetching] = useState(false);

  // Hydrate from localStorage AFTER hydration to prevent SSR mismatch
  useEffect(() => {
    try {
      const p = localStorage.getItem('nf_portfolios');
      if (p) setPortfolios(JSON.parse(p));
      
      const w = localStorage.getItem('nf_watchlist');
      if (w) setWatchlist(JSON.parse(w));
      
      const i = localStorage.getItem('nf_indices');
      if (i) setIndices(JSON.parse(i));
    } catch (e) {
      console.error("Failed to parse cached data", e);
    }
  }, []);

  const refreshData = async () => {
    if (!user) return;
    setIsFetching(true);
    try {
      const [portsRes, watchRes, indRes] = await Promise.all([
        api.get('/portfolios').catch(() => ({ data: portfolios })),
        api.get('/watchlist').catch(() => ({ data: watchlist })),
        api.get('/securities/indices').catch(() => ({ data: indices }))
      ]);

      setPortfolios(portsRes.data);
      setWatchlist(watchRes.data);
      setIndices(indRes.data);

      if (typeof window !== 'undefined') {
        localStorage.setItem('nf_portfolios', JSON.stringify(portsRes.data));
        localStorage.setItem('nf_watchlist', JSON.stringify(watchRes.data));
        localStorage.setItem('nf_indices', JSON.stringify(indRes.data));
      }
    } catch (err) {
      console.error("Failed to refresh global data:", err);
    } finally {
      setIsFetching(false);
    }
  };

  // Fetch as soon as user is authenticated
  useEffect(() => {
    if (user) {
      refreshData();
    }
  }, [user]);

  return (
    <GlobalDataContext.Provider value={{ portfolios, watchlist, indices, refreshData, isFetching }}>
      {children}
    </GlobalDataContext.Provider>
  );
};

export const useGlobalData = () => useContext(GlobalDataContext);
