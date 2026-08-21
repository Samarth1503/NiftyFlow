"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useGlobalData } from "@/context/GlobalDataContext";
import api from "@/lib/api";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { ChevronDown, Plus, ExternalLink, Clock } from "lucide-react";

export default function Dashboard() {
  const router = useRouter();
  const { indices, portfolios, watchlist } = useGlobalData();
  const safeIndices = Array.isArray(indices) ? indices : [];

  // Chart State (Real NIFTY 50 Data)
  const timeframes = ["1M", "3M", "6M", "YTD", "1Y", "5Y", "MAX"];
  const [activeTimeframe, setActiveTimeframe] = useState("1M");
  const [chartData, setChartData] = useState<any[]>([]);
  const [niftyData, setNiftyData] = useState<any>(null);

  // News State
  const [news, setNews] = useState<any[]>([]);

  // Calculate Chart Direction based on actual data
  const chartDirection = useMemo(() => {
    if (chartData.length < 2) return 'neutral';
    
    // Find first valid price
    let firstPrice = null;
    for (let i = 0; i < chartData.length; i++) {
        if (chartData[i].close !== null && chartData[i].close !== undefined) {
            firstPrice = chartData[i].close;
            break;
        }
    }
    
    // Find last valid price
    let lastPrice = null;
    for (let i = chartData.length - 1; i >= 0; i--) {
        if (chartData[i].close !== null && chartData[i].close !== undefined) {
            lastPrice = chartData[i].close;
            break;
        }
    }
    
    if (firstPrice === null || lastPrice === null) return 'neutral';
    if (lastPrice > firstPrice) return 'up';
    if (lastPrice < firstPrice) return 'down';
    return 'neutral';
  }, [chartData]);

  const chartColor = chartDirection === 'up' ? '#90e58c' : (chartDirection === 'down' ? '#ff5662' : '#9aa0a6');

  // Format Last Updated Timestamp
  const formattedTimestamp = useMemo(() => {
      if (!niftyData || !niftyData.timestamp) return "Last updated: Unavailable";
      
      try {
          const dt = new Date(niftyData.timestamp);
          const options: Intl.DateTimeFormatOptions = { 
              day: 'numeric', 
              month: 'short', 
              year: 'numeric', 
              hour: 'numeric', 
              minute: '2-digit', 
              hour12: true 
          };
          return `Last updated: ${dt.toLocaleString('en-IN', options)}`;
      } catch (e) {
          return "Last updated: Unavailable";
      }
  }, [niftyData]);

  // Fetch NIFTY 50 History
  useEffect(() => {
    let period = "1mo";
    if (activeTimeframe === "3M") period = "3mo";
    else if (activeTimeframe === "6M") period = "6mo";
    else if (activeTimeframe === "YTD") period = "ytd";
    else if (activeTimeframe === "1Y") period = "1y";
    else if (activeTimeframe === "5Y") period = "5y";
    else if (activeTimeframe === "MAX") period = "max";
    
    api.get(`/securities/symbol/%5ENSEI/history?period=${period}`)
      .then(res => {
          const formatted = res.data.map((d: any) => ({
              date: new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
              close: d.price
          }));
          setChartData(formatted);
      })
      .catch(console.error);
  }, [activeTimeframe]);

  // Set Nifty Data from indices
  useEffect(() => {
    const n50 = safeIndices.find(idx => idx.symbol === "^NSEI");
    if (n50) setNiftyData(n50);
  }, [safeIndices]);

  // Fetch News
  useEffect(() => {
    api.get("/news").then(res => setNews(res.data)).catch(console.error);
  }, []);

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl pb-12">
      


      {/* Index Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {safeIndices.slice(0, 3).map((idx, i) => (
          <div 
            key={i} 
            onClick={() => idx.symbol && router.push(`/stocks/${encodeURIComponent(idx.symbol)}`)}
            className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-5 cursor-pointer hover:bg-[#3c4043] transition-colors flex flex-col justify-between h-36"
          >
            <div>
              <div className="text-sm text-[var(--foreground)] mb-1">{idx.name}</div>
              <div className="text-2xl font-medium tracking-tight mb-1">{idx.current_price?.toLocaleString()}</div>
              <div className={`text-sm font-medium ${(idx.change != null && idx.change > 0) ? 'text-[#90e58c]' : 'text-[#ffa9af]'}`}>
                {idx.change != null && idx.change > 0 ? '+' : ''}{Number(idx.change || 0).toFixed(2)} ({idx.change_percent != null && idx.change_percent > 0 ? '+' : ''}{Number(idx.change_percent || 0).toFixed(2)}%)
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Charting Area */}
      <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-medium text-[var(--foreground)]">{niftyData?.name || "NIFTY 50"}</h2>
            <div className="flex items-end gap-3 mt-1">
              <span className="text-3xl font-medium tracking-tight">{niftyData?.price || "..."}</span>
              <span className={`text-lg font-medium pb-0.5 ${niftyData?.isUp ? 'text-[#90e58c]' : 'text-[#ffa9af]'}`}>
                {niftyData?.change || "..."} ({niftyData?.percent || "..."})
              </span>
            </div>
            {/* Last Updated Timestamp */}
            <div className="text-xs text-[var(--gf-gray-text)] mt-2 flex items-center gap-1">
              <Clock size={12} />
              {formattedTimestamp}
            </div>
          </div>
          
          <div className="flex gap-2">
            {["Area", "Compare", "Indicators"].map(btn => (
              <button key={btn} className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#3c4043] text-sm font-medium hover:bg-[#4a4d51] transition-colors border border-[var(--gf-border)]">
                {btn === "Area" && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M7 14l5-5 5 5 4-4"/></svg>}
                {btn}
                <ChevronDown size={14} className="text-[var(--gf-gray-text)]" />
              </button>
            ))}
          </div>
        </div>

        <div className="h-[400px] w-full mt-4 -ml-4 relative">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColor} stopOpacity={0.6}/>
                    <stop offset="95%" stopColor={chartColor} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#3c4043" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  stroke="#9aa0a6" 
                  tick={{fill: '#9aa0a6', fontSize: 12}} 
                  tickMargin={10} 
                  minTickGap={30}
                />
                <YAxis 
                  domain={['auto', 'auto']} 
                  stroke="#9aa0a6" 
                  tick={{fill: '#9aa0a6', fontSize: 12}}
                  tickFormatter={(val) => `₹${val.toLocaleString()}`}
                  width={80}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#303134', border: '1px solid #3c4043', borderRadius: '8px' }}
                  itemStyle={{ color: '#e8eaed' }}
                  labelStyle={{ color: '#9aa0a6' }}
                  formatter={(value: any) => [`₹${value.toFixed(2)}`, 'Close']}
                />
                <Area 
                  type="monotone" 
                  dataKey="close" 
                  stroke={chartColor} 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorValue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-[var(--gf-gray-text)]">
              Loading Chart Data...
            </div>
          )}
        </div>

        {/* Timeframe Pills */}
        <div className="flex gap-4 mt-6">
          {timeframes.map(tf => (
            <button
              key={tf}
              onClick={() => setActiveTimeframe(tf)}
              className={`text-sm font-medium px-3 py-1 rounded-full transition-colors ${
                activeTimeframe === tf 
                  ? "bg-[#4a4d51] text-white" 
                  : "text-[var(--gf-gray-text)] hover:text-white"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Data Tables (3-Column Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4">
        
        {/* Portfolios */}
        <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl overflow-hidden flex flex-col h-[400px]">
          <div className="p-4 border-b border-[var(--gf-border)] flex justify-between items-center">
            <h3 className="font-medium text-[var(--foreground)]">Your Portfolios</h3>
            <button onClick={() => window.dispatchEvent(new Event('open-create-portfolio'))} className="text-[var(--gf-blue)] text-sm hover:underline flex items-center gap-1">
              <Plus size={14} /> Create
            </button>
          </div>
          <div className="flex flex-col overflow-y-auto scrollbar-hide">
            {portfolios.length === 0 ? (
              <div className="p-6 text-center text-[var(--gf-gray-text)] text-sm">
                No portfolios found.
              </div>
            ) : (
              portfolios.map((item, i) => (
                <div key={i} onClick={() => router.push(`/portfolio/${item.id}`)} className="flex justify-between items-center p-4 hover:bg-[#3c4043] cursor-pointer border-b border-[var(--gf-border)] last:border-0 transition-colors">
                  <div className="font-medium text-[var(--foreground)] text-sm">{item.name}</div>
                  <ChevronDown size={16} className="-rotate-90 text-[var(--gf-gray-text)]" />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Watchlist */}
        <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl overflow-hidden flex flex-col h-[400px]">
          <div className="p-4 border-b border-[var(--gf-border)]">
            <h3 className="font-medium text-[var(--foreground)]">Watchlist</h3>
          </div>
          <div className="flex flex-col overflow-y-auto scrollbar-hide">
            {watchlist.length === 0 ? (
              <div className="p-6 text-center text-[var(--gf-gray-text)] text-sm">
                Your watchlist is empty. Search for stocks above.
              </div>
            ) : (
              watchlist.map((item, i) => (
                <div key={i} onClick={() => router.push(`/stocks/${encodeURIComponent(item.symbol)}`)} className="flex justify-between items-center p-4 hover:bg-[#3c4043] cursor-pointer border-b border-[var(--gf-border)] last:border-0 transition-colors">
                  <div>
                    <div className="font-medium text-[var(--foreground)] text-sm">{item.symbol}</div>
                    <div className="text-xs text-[var(--gf-gray-text)] mt-0.5 truncate max-w-[120px]">{item.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-[var(--foreground)]">View</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Market News */}
        <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl overflow-hidden flex flex-col h-[400px]">
          <div className="p-4 border-b border-[var(--gf-border)]">
            <h3 className="font-medium text-[var(--foreground)]">Market News</h3>
          </div>
          <div className="flex flex-col overflow-y-auto scrollbar-hide">
            {news.length === 0 ? (
              <div className="p-6 text-center text-[var(--gf-gray-text)] text-sm">
                Loading news...
              </div>
            ) : (
              news.slice(0, 10).map((item, i) => (
                <a key={i} href={item.link} target="_blank" rel="noopener noreferrer" className="flex justify-between items-start p-4 hover:bg-[#3c4043] cursor-pointer border-b border-[var(--gf-border)] last:border-0 transition-colors">
                  <div className="flex-1 pr-3">
                    <div className="font-medium text-[var(--foreground)] text-sm line-clamp-2">{item.title}</div>
                    <div className="text-xs text-[var(--gf-gray-text)] mt-1">{item.publisher}</div>
                  </div>
                  <ExternalLink size={14} className="text-[var(--gf-gray-text)] flex-shrink-0 mt-0.5" />
                </a>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
