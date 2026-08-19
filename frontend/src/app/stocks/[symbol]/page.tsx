"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { ArrowLeft, Plus, TrendingDown, TrendingUp, ChevronDown, Activity, Layers } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface HistoricalData {
  timestamp: string;
  price: number;
}

interface StockDetails {
  id: number;
  symbol: string;
  name: string;
  exchange: string | null;
  current_price: number | null;
  previous_close: number | null;
  change: number | null;
  change_percent: number | null;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  volume: number | null;
  avg_volume: number | null;
  fifty_two_wk_low: number | null;
  eps: number | null;
  last_updated: string | null;
  historical_1m: HistoricalData[];
}

export default function StockDetailsPage() {
  const { symbol } = useParams();
  const router = useRouter();
  
  const [stock, setStock] = useState<StockDetails | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [timeframe, setTimeframe] = useState("6M");
  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchlistLoading, setWatchlistLoading] = useState(false);

  const [activeTab, setActiveTab] = useState("Overview");
  const [financials, setFinancials] = useState<any>(null);
  const [financialsLoading, setFinancialsLoading] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    const cleanSymbol = decodeURIComponent(Array.isArray(symbol) ? symbol[0] : symbol).toUpperCase();
    
    let period = "6mo";
    if (timeframe === "1M") period = "1mo";
    else if (timeframe === "YTD") period = "ytd";
    else if (timeframe === "MAX") period = "max";
    else period = "6mo";

    api.get(`/securities/symbol/${encodeURIComponent(cleanSymbol)}/history?period=${period}`)
      .then(res => setHistory(res.data))
      .catch(console.error);
  }, [symbol, timeframe]);


  useEffect(() => {
    if (!symbol) return;
    
    // Convert symbol to string, decode it (for indices like ^NSEI), uppercase it
    const cleanSymbol = decodeURIComponent(Array.isArray(symbol) ? symbol[0] : symbol).toUpperCase();

    const fetchStock = async () => {
      setLoading(true);
      try {
        const [response, wlResponse] = await Promise.all([
          api.get(`/securities/symbol/${encodeURIComponent(cleanSymbol)}`),
          api.get('/watchlist')
        ]);
        
        setStock(response.data);
        setError(null);
        
        // Also check if it's in the watchlist
        const wl = wlResponse.data;
        if (wl.some((s: any) => s.symbol === cleanSymbol)) {
          setInWatchlist(true);
        }
      } catch (err: any) {
        console.error("Error fetching stock:", err);
        if (err.response?.status === 404) {
          setError(`Stock "${cleanSymbol}" not found.`);
        } else {
          setError("Failed to fetch stock details. Please try again later.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStock();
  }, [symbol]);

  useEffect(() => {
    if (!symbol) return;
    
    const cleanSymbol = decodeURIComponent(Array.isArray(symbol) ? symbol[0] : symbol).toUpperCase();
    if ((activeTab === "Earnings" || activeTab === "Financials") && !financials && !financialsLoading) {
      setFinancialsLoading(true);
      api.get(`/securities/symbol/${encodeURIComponent(cleanSymbol)}/financials`)
        .then(res => setFinancials(res.data))
        .catch(console.error)
        .finally(() => setFinancialsLoading(false));
    }
  }, [activeTab, symbol, financials, financialsLoading]);

  const toggleWatchlist = async () => {
    if (!stock) return;
    setWatchlistLoading(true);
    try {
      if (inWatchlist) {
        await api.delete(`/watchlist/${stock.symbol}`);
        setInWatchlist(false);
      } else {
        await api.post(`/watchlist/${stock.symbol}`);
        setInWatchlist(true);
      }
    } catch (error) {
      console.error("Failed to update watchlist", error);
      alert("Failed to update watchlist.");
    } finally {
      setWatchlistLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1F1F1F] text-white flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-gray-400">Loading stock details...</p>
        </div>
      </div>
    );
  }

  if (error || !stock) {
    return (
      <div className="min-h-screen bg-[#1F1F1F] text-white flex flex-col items-center justify-center">
        <Activity className="w-16 h-16 text-gray-600 mb-4" />
        <h1 className="text-2xl font-semibold mb-2">Stock Not Found</h1>
        <p className="text-gray-400 mb-6">{error || "The requested stock symbol does not exist in our database."}</p>
        <Link href="/dashboard" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-md font-medium transition-colors">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const isUp = (stock.change ?? 0) >= 0;
  const colorClass = isUp ? "text-[#34A853]" : "text-[#EA4335]";
  const chartColor = isUp ? "#34A853" : "#EA4335";

  // Formatting helpers
  const formatNum = (num: number | null, fallback = "-") => num !== null && num !== undefined ? num.toLocaleString('en-IN') : fallback;
  const formatPrice = (num: number | null) => num !== null && num !== undefined ? `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-";

  // Filter history based on timeframe
  const getDisplayHistory = () => {
    if (!history || history.length === 0) return [];
    
    const now = new Date();
    let startDate = new Date();
    
    if (timeframe === "1M") {
      startDate.setMonth(now.getMonth() - 1);
    } else if (timeframe === "6M") {
      startDate.setMonth(now.getMonth() - 6);
    } else if (timeframe === "YTD") {
      startDate = new Date(now.getFullYear(), 0, 1);
    } else {
      return history; // MAX
    }
    
    return history.filter(item => new Date(item.date) >= startDate);
  };
  
  const displayHistory = getDisplayHistory();

  return (
    <div className="min-h-screen bg-[#1F1F1F] text-white pb-12">
      {/* Header mapping to the mockup */}
      <div className="flex flex-col max-w-[1200px] mx-auto pt-6 px-4 md:px-8">
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center text-sm text-gray-300 mb-6 space-x-2 font-medium">
          <Link href="/dashboard" className="flex items-center hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Home
          </Link>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">{stock.symbol}:{stock.exchange || 'NSE'}</span>
        </div>
        
        {/* Title block */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div className="flex items-center">
            <div className="w-12 h-12 rounded-full bg-[#303134] border border-[#3C4043] flex items-center justify-center font-bold text-xl mr-4 shadow-sm text-gray-200">
              {stock.name.charAt(0).toUpperCase()}
            </div>
            <h1 className="text-2xl md:text-3xl font-medium tracking-tight text-gray-100">{stock.name}</h1>
          </div>
            <button 
              onClick={toggleWatchlist}
              disabled={watchlistLoading}
              className={`px-4 py-2 rounded-full flex items-center border text-sm font-medium transition-colors hover:scale-105 active:scale-95 ${
                watchlistLoading 
                  ? 'opacity-50 cursor-not-allowed border-[#3C4043] bg-[#303134]' 
                  : inWatchlist 
                    ? 'border-[var(--gf-blue)] text-[var(--gf-blue)] hover:bg-[#303134] bg-transparent'
                    : 'border-[#3C4043] hover:bg-[#3c4043] bg-[#303134]'
              }`}
            >
              {watchlistLoading ? (
                <span>Updating...</span>
              ) : inWatchlist ? (
                <>★ <span className="ml-2">Remove from Watchlist</span></>
              ) : (
                <><Plus className="w-4 h-4 mr-2" /> Add to Watchlist</>
              )}
            </button>
        </div>
        
        {/* Price block */}
        <div className="mb-8">
          <div className="text-4xl md:text-5xl font-semibold mb-2 tracking-tight">
            {formatPrice(stock.current_price)}
          </div>
          <div className={`flex items-center font-medium ${colorClass}`}>
            {isUp ? <TrendingUp className="w-5 h-5 mr-1" /> : <TrendingDown className="w-5 h-5 mr-1" />}
            {stock.change_percent !== null ? `${isUp ? '+' : ''}${stock.change_percent.toFixed(2)}%` : "-"} 
            <span className="ml-1 opacity-90">
              ({isUp ? '+' : ''}{formatPrice(stock.change)}) Today
            </span>
          </div>
          <div className="text-gray-500 text-sm mt-1.5 font-medium">
            {stock.last_updated ? new Date(stock.last_updated).toLocaleString('en-IN') : "Live Market"} · INR
          </div>
        </div>
        
        {/* Content Card */}
        <div className="bg-[#202124] rounded-2xl border border-[#3C4043] overflow-hidden shadow-lg transition-transform duration-300">
          
          {/* Chart Tool Actions (Mocked to match image) */}
          <div className="flex space-x-6 p-4 border-b border-[#3C4043] text-sm font-medium text-gray-400">
            <button className="flex items-center hover:text-white transition-colors"><Activity className="w-4 h-4 mr-2"/> Area <ChevronDown className="w-3 h-3 ml-1" /></button>
            <button className="flex items-center hover:text-white transition-colors"><Layers className="w-4 h-4 mr-2"/> Compare <ChevronDown className="w-3 h-3 ml-1" /></button>
          </div>
          
          {/* Main Chart Area */}
          <div className="h-[320px] p-4 pt-8 relative">
             {displayHistory && displayHistory.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={displayHistory}>
                     <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={chartColor} stopOpacity={0.25}/>
                          <stop offset="95%" stopColor={chartColor} stopOpacity={0}/>
                        </linearGradient>
                     </defs>
                     <Tooltip 
                        contentStyle={{ backgroundColor: '#303134', border: 'none', borderRadius: '8px', color: '#fff' }}
                        itemStyle={{ color: chartColor, fontWeight: 500 }}
                        formatter={(value: any) => [formatPrice(Number(value)), "Price"]}
                        labelFormatter={(label: any) => new Date(label).toLocaleDateString()}
                     />
                     <XAxis 
                        dataKey="date" 
                        hide 
                     />
                     <YAxis 
                        domain={['auto', 'auto']} 
                        hide 
                     />
                     <Area 
                        type="monotone" 
                        dataKey="price" 
                        stroke={chartColor} 
                        strokeWidth={2}
                        fillOpacity={1} 
                        fill="url(#colorPrice)" 
                     />
                  </AreaChart>
               </ResponsiveContainer>
             ) : (
                <div className="flex items-center justify-center h-full text-gray-500 flex-col">
                  <Activity className="w-12 h-12 mb-4 opacity-20" />
                  <p>No historical data available.</p>
                  <button onClick={() => api.post(`/securities/${stock.id}/refresh`).then(() => window.location.reload())} className="mt-4 px-4 py-2 bg-[var(--gf-surface)] hover:bg-[#3c4043] rounded-full text-sm">
                    Trigger Refresh
                  </button>
                </div>
             )}
          </div>
          
          {/* Timeframe Selectors */}
          <div className="flex px-4 py-3 space-x-4 border-b border-[#3C4043] text-sm font-medium text-gray-400 overflow-x-auto">
             {["1M", "6M", "YTD", "MAX"].map((tf) => (
               <button 
                 key={tf}
                 onClick={() => setTimeframe(tf)}
                 className={`px-3 py-1 rounded-full transition-colors ${
                   timeframe === tf 
                     ? "bg-[#4285F4] text-white" 
                     : "hover:text-white"
                 }`}
               >
                 {tf}
               </button>
             ))}
          </div>

          {/* Tabs */}
          <div className="flex border-b border-[#3C4043] px-2">
             {["Overview", "Earnings", "Financials"].map(tab => (
               <div 
                 key={tab}
                 onClick={() => setActiveTab(tab)}
                 className={`px-6 py-4 font-medium cursor-pointer transition-colors ${
                   activeTab === tab 
                     ? 'border-b-2 border-[#8AB4F8] text-[#8AB4F8]' 
                     : 'text-gray-400 hover:text-gray-200'
                 }`}
               >
                 {tab}
               </div>
             ))}
          </div>
          
          {/* Details Content */}
          <div className="p-6 md:p-8">
             {activeTab === "Overview" && (
               <div className="grid grid-cols-2 md:grid-cols-4 gap-y-8 gap-x-6 text-sm">
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">Open</div>
                     <div className="text-gray-200 font-medium">{formatPrice(stock.open_price)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">High</div>
                     <div className="text-gray-200 font-medium">{formatPrice(stock.high_price)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">Low</div>
                     <div className="text-gray-200 font-medium">{formatPrice(stock.low_price)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">Prev. close</div>
                     <div className="text-gray-200 font-medium">{formatPrice(stock.previous_close)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">Volume</div>
                     <div className="text-gray-200 font-medium">{formatNum(stock.volume)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">Avg. vol.</div>
                     <div className="text-gray-200 font-medium">{formatNum(stock.avg_volume)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">52-wk low</div>
                     <div className="text-gray-200 font-medium">{formatPrice(stock.fifty_two_wk_low)}</div>
                  </div>
                  <div>
                     <div className="text-gray-400 mb-1.5 font-medium">EPS</div>
                     <div className="text-gray-200 font-medium">{formatPrice(stock.eps)}</div>
                  </div>
               </div>
             )}

             {activeTab === "Earnings" && (
               <div className="text-sm">
                 {financialsLoading ? (
                   <div className="text-gray-400">Loading earnings data...</div>
                 ) : financials?.earnings && Object.keys(financials.earnings).length > 0 ? (
                   <div className="overflow-x-auto">
                     <table className="w-full text-left border-collapse">
                       <thead>
                         <tr className="border-b border-[#3C4043] text-gray-400">
                           <th className="py-3 px-4 font-medium">Date</th>
                           <th className="py-3 px-4 font-medium">EPS Estimate</th>
                           <th className="py-3 px-4 font-medium">Reported EPS</th>
                           <th className="py-3 px-4 font-medium">Surprise %</th>
                         </tr>
                       </thead>
                       <tbody>
                         {Object.entries(financials.earnings).map(([dateStr, data]: [string, any], idx) => (
                           <tr key={idx} className="border-b border-[#303134] hover:bg-[#303134] transition-colors">
                             <td className="py-3 px-4">{new Date(dateStr).toLocaleDateString()}</td>
                             <td className="py-3 px-4">{data['EPS Estimate'] ? formatPrice(data['EPS Estimate']) : '-'}</td>
                             <td className="py-3 px-4">{data['Reported EPS'] ? formatPrice(data['Reported EPS']) : '-'}</td>
                             <td className="py-3 px-4 text-[var(--gf-green)]">{data['Surprise(%)'] ? (data['Surprise(%)'] * 100).toFixed(2) + '%' : '-'}</td>
                           </tr>
                         ))}
                       </tbody>
                     </table>
                   </div>
                 ) : (
                   <div className="text-gray-400">No earnings data available.</div>
                 )}
               </div>
             )}

             {activeTab === "Financials" && (
               <div className="text-sm">
                 {financialsLoading ? (
                   <div className="text-gray-400">Loading financials data...</div>
                 ) : financials?.financials && Object.keys(financials.financials).length > 0 ? (
                   <div className="overflow-x-auto">
                     <table className="w-full text-left border-collapse">
                       <thead>
                         <tr className="border-b border-[#3C4043] text-gray-400">
                           <th className="py-3 px-4 font-medium">Metric</th>
                           {Object.keys(financials.financials).slice(0, 4).map(dateStr => (
                             <th key={dateStr} className="py-3 px-4 font-medium whitespace-nowrap">{dateStr}</th>
                           ))}
                         </tr>
                       </thead>
                       <tbody>
                         {['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income'].map(metric => (
                           <tr key={metric} className="border-b border-[#303134] hover:bg-[#303134] transition-colors">
                             <td className="py-3 px-4 font-medium text-gray-200">{metric}</td>
                             {Object.keys(financials.financials).slice(0, 4).map(dateStr => (
                               <td key={dateStr} className="py-3 px-4 text-gray-400">
                                 {financials.financials[dateStr][metric] ? formatNum(financials.financials[dateStr][metric]) : '-'}
                               </td>
                             ))}
                           </tr>
                         ))}
                       </tbody>
                     </table>
                   </div>
                 ) : (
                   <div className="text-gray-400">No financial statement data available.</div>
                 )}
               </div>
             )}
          </div>
        </div>
      </div>
    </div>
  );
}
