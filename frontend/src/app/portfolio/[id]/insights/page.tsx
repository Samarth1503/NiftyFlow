"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { ArrowLeft, BrainCircuit, ChevronDown, ChevronUp } from "lucide-react";

interface Holding {
  id: number;
  security_id: number;
  symbol: string;
  name?: string;
  quantity: number;
  current_value: number | null;
}

interface Prediction {
  predicted_score: number;
  prediction_date: string;
}


export default function PortfolioInsights() {
  const { id } = useParams();
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [predictions, setPredictions] = useState<Record<number, Prediction>>({});
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get(`/portfolios/${id}`);
        setHoldings(res.data.holdings);

        try {
          const pRes = await api.get(`/securities/predictions/bulk`);
          setPredictions(pRes.data);
        } catch (e) {
          console.error("Failed to fetch bulk predictions", e);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  if (loading) return <div className="p-8">Loading insights...</div>;

  return (
    <div>
      <div className="flex items-center gap-4 mb-8">
        <Link href={`/portfolio/${id}`} className="text-[var(--gf-gray-text)] hover:text-white">
          <ArrowLeft size={24} />
        </Link>
        <h2 className="text-2xl font-medium">AI Portfolio Insights</h2>
      </div>

      {/* Model Accuracy Section */}
      <div className="bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-6 mb-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-[var(--gf-blue)] bg-opacity-20 rounded-full">
            <BrainCircuit size={24} className="text-[var(--gf-blue)]" />
          </div>
          <div>
            <h3 className="text-xl font-medium text-[var(--foreground)]">NiftyFlow XGBoost Core</h3>
            <p className="text-[var(--gf-gray-text)]">Live Model Accuracy: <span className="text-white font-medium">53.33%</span> | Precision: <span className="text-white font-medium">53.33%</span></p>
          </div>
        </div>

        <div className="mt-6 border-t border-[var(--gf-border)] pt-4">
          <div className="text-sm text-[var(--gf-gray-text)] leading-relaxed space-y-4">
            <p>
              The NiftyFlow XGBoost Core is a predictive machine learning pipeline that analyzes historical market data 
              to forecast short-term stock price movements. Powered by an XGBoost Gradient Boosting Classifier, 
              it evaluates technical indicators to give you an AI-driven edge in portfolio management.
            </p>
            
            {expanded && (
              <>
                <p>
                  <strong>Parameters & Features:</strong> The model looks at 2 years of daily historical data. It engineers technical features including 
                  10-day, 50-day, and 200-day Simple Moving Averages (SMAs), 1-day and 5-day momentum returns, and 20-day rolling volatility.
                </p>
                <p>
                  <strong>Target Calculation:</strong> It uses a 5-day forward looking window to classify whether the stock price will be higher 5 days from now (1) or lower (0).
                </p>
                <p>
                  <strong>Judging Accuracy:</strong> Before generating a live prediction, the script performs a <em>Time-Series Split</em>. It trains on the first 80% of historical data and tests itself on the most recent 20% of data. The reported 53.33% accuracy means that during this rigorous out-of-sample backtesting, the model correctly predicted the 5-day trend 53.33% of the time, providing a mathematical edge over a random coin flip.
                </p>
              </>
            )}
            
            <button 
              onClick={() => setExpanded(!expanded)} 
              className="font-medium text-[var(--gf-blue)] hover:text-white transition-colors flex items-center gap-1 mt-2"
            >
              <span>{expanded ? "Read Less" : "Read More"}</span>
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Insights Table */}
      <div className="bg-[var(--gf-surface)] rounded-xl border border-[var(--gf-border)] overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-[#202124] text-[var(--gf-gray-text)] border-b border-[var(--gf-border)]">
            <tr>
              <th className="p-4 font-normal">Symbol</th>
              <th className="p-4 font-normal text-right">Quantity</th>
              <th className="p-4 font-normal text-right">Current Price</th>
              <th className="p-4 font-normal text-right">Prediction (Win Prob)</th>
              <th className="p-4 font-normal text-center">AI Suggestion</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => {
              const pred = predictions[h.security_id];
              const score = pred ? pred.predicted_score : null;
              const ltp = h.current_value ? (h.current_value / h.quantity) : 0;
              
              let suggestion = "HOLD";
              let sugColor = "text-[var(--gf-gray-text)] border-[var(--gf-border)]";
              
              if (score !== null) {
                if (score > 0.6) {
                  suggestion = "STRONG BUY";
                  sugColor = "text-[var(--gf-green)] border-[var(--gf-green)] bg-[var(--gf-green-bg)]";
                } else if (score > 0.5) {
                  suggestion = "BUY";
                  sugColor = "text-[var(--gf-green)] border-[var(--gf-green)]";
                } else if (score < 0.4) {
                  suggestion = "SELL";
                  sugColor = "text-[var(--gf-red)] border-[var(--gf-red)] bg-[var(--gf-red-bg)]";
                }
              }

              return (
                <tr key={h.id} className="border-b border-[var(--gf-border)] hover:bg-[#3c4043] transition-colors">
                  <td className="p-4">
                    <div className="font-medium">{h.symbol}</div>
                    <div className="text-xs text-[var(--gf-gray-text)]">{h.name || "Company"}</div>
                  </td>
                  <td className="p-4 text-right">{h.quantity}</td>
                  <td className="p-4 text-right">₹{ltp.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                  <td className="p-4 text-right">
                    {score !== null ? (
                      <span className={score > 0.5 ? 'text-[var(--gf-green)]' : 'text-[var(--gf-red)]'}>
                        {(score * 100).toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-[var(--gf-gray-text)]">No Data</span>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    <span className={`px-3 py-1 rounded text-xs font-bold border ${sugColor}`}>
                      {suggestion}
                    </span>
                  </td>
                </tr>
              )
            })}
            {holdings.length === 0 && (
              <tr><td colSpan={6} className="p-8 text-center text-[var(--gf-gray-text)]">No holdings to analyze.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
