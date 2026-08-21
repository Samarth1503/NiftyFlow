"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useGlobalData } from "@/context/GlobalDataContext";

export default function CreatePortfolioModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { refreshData } = useGlobalData();

  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener("open-create-portfolio", handleOpen);
    return () => window.removeEventListener("open-create-portfolio", handleOpen);
  }, []);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setLoading(true);
    try {
      await api.post("/portfolios", { name, description });
      await refreshData();
      setIsOpen(false);
      setName("");
      setDescription("");
    } catch (err: unknown) {
      console.error(err);
      setError((err as any).response?.data?.detail || "Failed to create portfolio");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#28292c] border border-[var(--gf-border)] w-full max-w-md rounded-xl shadow-2xl p-6">
        <h2 className="text-xl font-medium mb-4 text-[var(--foreground)]">Create Portfolio</h2>
        {error && <div className="bg-[var(--gf-red-bg)] text-[var(--gf-red)] px-3 py-2 rounded mb-4 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--gf-gray-text)] mb-1">Portfolio Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#101218] border border-[var(--gf-border)] rounded-lg px-3 py-2 text-sm text-[var(--foreground)] outline-none focus:border-[var(--gf-blue)] transition-colors"
              placeholder="e.g. Retirement Fund"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--gf-gray-text)] mb-1">Description (Optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-[#101218] border border-[var(--gf-border)] rounded-lg px-3 py-2 text-sm text-[var(--foreground)] outline-none focus:border-[var(--gf-blue)] transition-colors"
              placeholder="Long term tech stocks..."
            />
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 text-sm font-medium text-[var(--gf-gray-text)] hover:text-[var(--foreground)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-[var(--gf-blue)] text-black px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90 disabled:opacity-50 transition-colors"
            >
              {loading ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
