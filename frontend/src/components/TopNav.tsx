"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Search, Mic } from "lucide-react";
import api from "@/lib/api";
import LogoutButton from "./LogoutButton";

export default function TopNav() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    
    timeoutRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.get(`/securities/search?q=${encodeURIComponent(query)}`);
        setResults(res.data);
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [query]);

  const handleSelect = (symbol: string) => {
    setQuery("");
    setIsFocused(false);
    router.push(`/stocks/${symbol}`);
  };

  return (
    <header className="sticky top-0 z-50 bg-[var(--background)] py-4 flex justify-between items-center border-b border-[var(--gf-border)] mb-6">
      <div className="flex items-center w-full justify-between">
        
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-90 transition-opacity min-w-[200px]">
          <Image src="/icon.jpg" width={32} height={32} className="rounded-full" alt="NiftyFlow Logo" />
          <h1 className="text-xl font-bold tracking-tight text-[var(--foreground)]">NiftyFlow</h1>
        </Link>
        
        {/* Search Bar */}
        <div className="flex-1 max-w-2xl px-8 relative">
          <div className={`flex items-center gap-2 bg-[var(--gf-surface)] rounded-full px-4 py-2.5 transition-colors border ${isFocused ? 'border-[var(--gf-gray-text)]' : 'border-transparent'}`}>
            <Search size={20} className="text-[var(--gf-gray-text)]" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setTimeout(() => setIsFocused(false), 200)}
              placeholder="Search stocks, indices..."
              className="bg-transparent flex-1 outline-none text-sm text-[var(--foreground)]"
            />
            <Mic size={20} className="text-[var(--gf-gray-text)] cursor-pointer hover:text-white transition-colors" />
          </div>

          {/* Search Dropdown */}
          {isFocused && query.trim() && (
            <div className="absolute top-full left-8 right-8 mt-2 bg-[#303134] border border-[var(--gf-border)] rounded-xl overflow-hidden shadow-2xl z-50">
              {loading ? (
                <div className="p-4 text-center text-[var(--gf-gray-text)] text-sm">Searching...</div>
              ) : results.length > 0 ? (
                results.map(sec => (
                  <div 
                    key={sec.id}
                    className="px-4 py-3 hover:bg-[#3c4043] cursor-pointer text-sm flex justify-between items-center"
                    onClick={() => handleSelect(sec.symbol)}
                  >
                    <div>
                      <div className="font-medium text-[var(--foreground)]">{sec.symbol}</div>
                      <div className="text-xs text-[var(--gf-gray-text)] truncate">{sec.name}</div>
                    </div>
                    <div className="text-xs text-[var(--gf-gray-text)]">{sec.exchange}</div>
                  </div>
                ))
              ) : (
                <div className="p-4 text-center text-[var(--gf-gray-text)] text-sm">No results found</div>
              )}
            </div>
          )}
        </div>

        {/* Right Nav */}
        <div className="flex items-center min-w-[200px] justify-end">
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}
