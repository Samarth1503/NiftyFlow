"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Folder, Star, Plus } from "lucide-react";
import { useGlobalData } from "@/context/GlobalDataContext";

export default function Sidebar() {
  const pathname = usePathname();
  const { indices } = useGlobalData();
  const safeIndices = Array.isArray(indices) ? indices : [];

  const navItems = [
    { name: "Portfolios", icon: Folder, path: "/dashboard" },
    { name: "Watchlist", icon: Star, path: "/dashboard" },
  ];

  return (
    <aside className="w-64 flex-shrink-0 pr-6 border-r border-[var(--gf-border)] mr-8 hidden lg:block sticky top-[80px] h-[calc(100vh-100px)] overflow-y-auto scrollbar-hide">
      
      {/* Main Navigation */}
      <nav className="flex flex-col gap-1 mb-6">
        {navItems.map((item) => {
          const isActive = pathname === item.path || (pathname === '/' && item.name === 'Portfolios');
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.path}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? "bg-[var(--gf-surface)] text-[var(--foreground)]" : "text-[var(--gf-gray-text)] hover:bg-[var(--gf-surface)] hover:text-[var(--foreground)]"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon size={18} />
                <span>{item.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Create Portfolio Button */}
      <div className="px-3 mb-8">
        <button 
          className="w-full flex items-center justify-center gap-2 bg-[#3c4043] hover:bg-[#4a4d51] text-[var(--foreground)] py-2 rounded-full text-sm font-medium transition-colors"
          onClick={() => {
            window.dispatchEvent(new Event('open-create-portfolio'));
          }}
        >
          <Plus size={16} /> Create portfolio
        </button>
      </div>

      {/* Equity Sectors */}
      <div>
        <h3 className="px-3 text-xs font-bold text-[var(--gf-gray-text)] uppercase tracking-wider mb-3">Equity sectors</h3>
        <div className="flex flex-col gap-1">
          {safeIndices.map((idx, i) => {
            const isPositive = idx.change != null && idx.change > 0;
            return (
              <Link 
                key={i}
                href={`/stocks/${encodeURIComponent(idx.symbol || '')}`}
                className="flex items-center justify-between px-3 py-2 hover:bg-[var(--gf-surface)] rounded-lg transition-colors group"
              >
                <div>
                  <div className="text-sm font-medium text-[var(--foreground)] truncate max-w-[100px]">{idx.name}</div>
                  <div className="text-xs text-[var(--gf-gray-text)]">{idx.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-[var(--foreground)]">{idx.current_price?.toLocaleString()}</div>
                  <div className={`text-xs ${isPositive ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}`}>
                    {isPositive ? '+' : ''}{Number(idx.change || 0).toFixed(2)}
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

    </aside>
  );
}
