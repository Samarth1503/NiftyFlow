"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import { TrendingUp, TrendingDown, RefreshCcw, ArrowLeft } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useMemo } from "react";
import Link from "next/link";

interface Holding {
  id: number;
  security_id: number;
  symbol: string;
  quantity: number;
  average_buy_price: number;
  current_value: number | null;
  pnl: number | null;
  pnl_percent: number | null;
}

interface PortfolioDetail {
  id: number;
  name: string;
  total_invested: number;
  total_current: number;
  total_pnl: number;
  total_pnl_percent: number;
  holdings: Holding[];
}



const COLORS = ["#8ab4f8", "#f28b82", "#81c995", "#fde293", "#c58af9"];

export default function PortfolioPage() {
  const { id } = useParams();
  const [data, setData] = useState<PortfolioDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<any[]>([]);

  const [isAddingTxn, setIsAddingTxn] = useState(false);
  const [securities, setSecurities] = useState<any[]>([]);
  const [txnType, setTxnType] = useState("BUY");
  const [secId, setSecId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [txnDate, setTxnDate] = useState("");

  const fetchData = async () => {
    try {
      const [portRes, chartRes] = await Promise.all([
        api.get(`/portfolios/${id}`),
        api.get(`/portfolios/${id}/chart`)
      ]);
      setData(portRes.data);
      setChartData(chartRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    api.get("/securities").then(res => setSecurities(res.data)).catch(console.error);
  }, [id]);

  const handleAddTxn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!secId || !quantity || !price) return;
    
    const parsedQty = parseInt(quantity, 10);
    if (isNaN(parsedQty) || parsedQty <= 0 || parsedQty.toString() !== quantity) {
      alert("Quantity must be a positive whole number.");
      return;
    }

    try {
      const payload: any = {
        symbol: secId,
        transaction_type: txnType,
        quantity: parsedQty,
        price: parseFloat(price)
      };
      if (txnDate) {
        payload.timestamp = new Date(txnDate).toISOString();
      }
      
      await api.post(`/portfolios/${id}/transactions`, payload);
      setIsAddingTxn(false);
      setSecId(""); setQuantity(""); setPrice(""); setTxnDate("");
      // Refresh data
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to add transaction");
    }
  };

  if (loading || !data) return (
    <div className="p-8 max-w-[1200px] mx-auto animate-pulse">
      <div className="flex justify-between items-center mb-6">
        <div className="h-8 bg-[#3c4043] rounded w-64"></div>
        <div className="h-10 bg-[#3c4043] rounded w-40"></div>
      </div>
      <div className="h-80 bg-[#202124] rounded-xl border border-[var(--gf-border)] mb-8"></div>
      <div className="h-64 bg-[#202124] rounded-xl border border-[var(--gf-border)]"></div>
    </div>
  );

  // Calculate Totals
  
  return (
    <div>
      {isAddingTxn && (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center">
          <div className="bg-[var(--gf-surface)] p-6 rounded-xl border border-[var(--gf-border)] w-96 shadow-2xl">
            <h3 className="font-medium mb-4 text-lg">Add Transaction</h3>
            <form onSubmit={handleAddTxn} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs text-[var(--gf-gray-text)] mb-1">Type</label>
                <select value={txnType} onChange={e => setTxnType(e.target.value)} className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2 text-sm outline-none">
                  <option value="BUY">Buy</option>
                  <option value="SELL">Sell</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-[var(--gf-gray-text)] mb-1">Security</label>
                <input 
                  type="text"
                  list="securities-list"
                  value={secId} 
                  onChange={e => setSecId(e.target.value)} 
                  className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2 text-sm outline-none" 
                  placeholder="Enter stock symbol (e.g., INFY)"
                  required 
                />
                <datalist id="securities-list">
                  {securities.map(s => <option key={s.id} value={s.symbol}>{s.name}</option>)}
                </datalist>
              </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="block text-xs text-[var(--gf-gray-text)] mb-1">Quantity</label>
                    <input type="number" step="1" min="1" value={quantity} onChange={e => setQuantity(e.target.value)} className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2 text-sm outline-none" required />
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs text-[var(--gf-gray-text)] mb-1">Price (₹)</label>
                    <input type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2 text-sm outline-none" required />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-[var(--gf-gray-text)] mb-1">Date (Optional)</label>
                  <input type="date" value={txnDate} onChange={e => setTxnDate(e.target.value)} className="w-full bg-[var(--background)] border border-[var(--gf-border)] rounded-lg p-2 text-sm outline-none" />
                </div>
                <div className="flex justify-end gap-3 mt-2">
                  <button type="button" onClick={() => setIsAddingTxn(false)} className="px-4 py-2 text-sm text-[var(--gf-gray-text)] hover:text-white transition-colors">Cancel</button>
                  <button type="submit" className="px-4 py-2 text-sm bg-[var(--gf-blue)] text-black font-medium rounded-lg">Save</button>
                </div>
            </form>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-[var(--gf-gray-text)] hover:text-white">
            <ArrowLeft size={24} />
          </Link>
          <h2 className="text-2xl font-medium">{data.name}</h2>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setIsAddingTxn(true)} className="bg-[var(--gf-blue)] text-black px-4 py-2 rounded-full text-sm font-medium hover:opacity-90 transition-opacity">
            + Add Transaction
          </button>
          <Link href={`/portfolio/${id}/insights`}>
            <button className="bg-[var(--gf-surface)] border border-[var(--gf-border)] px-4 py-2 rounded-full text-sm font-medium hover:bg-[#3c4043] transition-colors">
              Portfolio Insights
            </button>
          </Link>
        </div>
      </div>

      {/* CHART SECTION */}
      <div className="bg-[var(--gf-surface)] rounded-xl border border-[var(--gf-border)] p-6 mb-8">
        <div className="flex items-center gap-4 mb-8 flex-wrap">
          {data.holdings.map((h, i) => (
            <div key={h.id} className="flex items-center gap-2 bg-[var(--background)] px-3 py-1.5 rounded-full border border-[var(--gf-border)] text-sm">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: COLORS[i % COLORS.length] }}></div>
              <span>{h.symbol}</span>
            </div>
          ))}
        </div>
        
        <div className="h-80 w-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorValuePort" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={(() => {
                      if (chartData.length < 2) return '#9aa0a6';
                      let first = chartData.find(d => d.value !== null && d.value !== undefined)?.value;
                      let last = [...chartData].reverse().find(d => d.value !== null && d.value !== undefined)?.value;
                      if (first == null || last == null) return '#9aa0a6';
                      if (last > first) return '#90e58c';
                      if (last < first) return '#ff5662';
                      return '#9aa0a6';
                  })()} stopOpacity={0.6}/>
                  <stop offset="95%" stopColor={(() => {
                      if (chartData.length < 2) return '#9aa0a6';
                      let first = chartData.find(d => d.value !== null && d.value !== undefined)?.value;
                      let last = [...chartData].reverse().find(d => d.value !== null && d.value !== undefined)?.value;
                      if (first == null || last == null) return '#9aa0a6';
                      if (last > first) return '#90e58c';
                      if (last < first) return '#ff5662';
                      return '#9aa0a6';
                  })()} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="var(--gf-gray-text)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--gf-gray-text)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val.toFixed(0)}`} domain={['auto', 'auto']} width={80} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#303134', border: '1px solid #3c4043', borderRadius: '8px' }}
                itemStyle={{ color: 'var(--foreground)' }}
                formatter={(value: any) => [`₹${Number(value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 'Portfolio Value']}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke={(() => {
                      if (chartData.length < 2) return '#9aa0a6';
                      let first = chartData.find(d => d.value !== null && d.value !== undefined)?.value;
                      let last = [...chartData].reverse().find(d => d.value !== null && d.value !== undefined)?.value;
                      if (first == null || last == null) return '#9aa0a6';
                      if (last > first) return '#90e58c';
                      if (last < first) return '#ff5662';
                      return '#9aa0a6';
                  })()} 
                strokeWidth={2} 
                fillOpacity={1}
                fill="url(#colorValuePort)"
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* TABLE SECTION */}
      <div className="bg-[var(--gf-surface)] rounded-xl border border-[var(--gf-border)] overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-[#202124] text-[var(--gf-gray-text)] border-b border-[var(--gf-border)]">
            <tr>
              <th className="p-4 font-normal">Symbol</th>
              <th className="p-4 font-normal text-right">Quantity</th>
              <th className="p-4 font-normal text-right">Avg Price</th>
              <th className="p-4 font-normal text-right">LTP</th>
              <th className="p-4 font-normal text-right">Invested Value</th>
              <th className="p-4 font-normal text-right">Current Value</th>
              <th className="p-4 font-normal text-right">Overall P/L</th>
              <th className="p-4 font-normal text-right">Overall P/L (%)</th>
            </tr>
          </thead>
          <tbody>
            {data.holdings.map((h) => {
              const ltp = h.current_value ? (h.current_value / h.quantity) : h.average_buy_price;
              const overallPos = (h.pnl || 0) >= 0;
              const investedValue = h.quantity * h.average_buy_price;
              const currentValue = h.current_value || investedValue;
              
              return (
                <tr key={h.id} className="border-b border-[var(--gf-border)] hover:bg-[#3c4043] transition-colors">
                  <td className="p-4 font-medium">{h.symbol}</td>
                  <td className="p-4 text-right">{h.quantity}</td>
                  <td className="p-4 text-right">₹{h.average_buy_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                  <td className="p-4 text-right">₹{ltp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                  <td className="p-4 text-right">₹{investedValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                  <td className="p-4 text-right">₹{currentValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                  
                  <td className={`p-4 text-right ${overallPos ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}`}>
                    {overallPos ? '+' : ''}₹{(h.pnl || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </td>
                  
                  <td className={`p-4 text-right ${overallPos ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}`}>
                    <div className={`inline-flex items-center gap-1 bg-[${overallPos ? 'var(--gf-green-bg)' : 'var(--gf-red-bg)'}] px-2 py-0.5 rounded`}>
                      {overallPos ? <TrendingUp size={14}/> : <TrendingDown size={14}/>} {(h.pnl_percent || 0).toFixed(2)}%
                    </div>
                  </td>
                </tr>
              )
            })}
            {/* TOTALS ROW */}
            {data.holdings.length > 0 && (
              <tr className="bg-[#202124] font-medium border-t-2 border-[var(--gf-border)]">
                <td className="p-4">Total</td>
                <td className="p-4 text-right">-</td>
                <td className="p-4 text-right">-</td>
                <td className="p-4 text-right">-</td>
                <td className="p-4 text-right">₹{data.total_invested.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                <td className="p-4 text-right">₹{data.total_current.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                <td className={`p-4 text-right ${data.total_pnl >= 0 ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}`}>
                  {data.total_pnl >= 0 ? '+' : ''}₹{data.total_pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </td>
                <td className="p-4 text-right">-</td>
                <td className={`p-4 text-right ${data.total_pnl >= 0 ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}`}>
                  {data.total_pnl >= 0 ? '+' : ''}{data.total_pnl_percent.toFixed(2)}%
                </td>
              </tr>
            )}
            {data.holdings.length === 0 && (
              <tr>
                <td colSpan={12} className="p-12 text-center text-[var(--gf-gray-text)]">
                  <div className="flex flex-col items-center justify-center">
                    <svg className="w-20 h-20 text-[var(--gf-border)] mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <p className="text-lg font-medium text-[var(--foreground)] mb-1">Your portfolio is empty</p>
                    <p className="text-sm">Add your first transaction to start tracking performance.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
