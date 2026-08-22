"use client";

import { useState } from "react";
import api from "@/lib/api";

export default function Contact() {
  const [formData, setFormData] = useState({ name: "", email: "", message: "" });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    try {
      await api.post("/contact", formData);
      setStatus("success");
      setFormData({ name: "", email: "", message: "" });
    } catch (error) {
      setStatus("error");
    }
  };

  return (
    <div className="max-w-xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-medium mb-8">Contact Us</h1>
      
      {status === "success" ? (
        <div className="bg-[var(--gf-surface)] border border-[var(--gf-green)] text-[var(--gf-green)] p-6 rounded-xl text-center">
          <p className="font-medium">Message sent successfully!</p>
          <p className="text-sm mt-2 opacity-80">We will get back to you as soon as possible.</p>
          <button 
            onClick={() => setStatus("idle")}
            className="mt-6 px-4 py-2 border border-[var(--gf-green)] rounded-lg hover:bg-[var(--gf-green)] hover:text-black transition-colors"
          >
            Send another message
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm text-[var(--gf-gray-text)] mb-2">Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-3 text-[var(--foreground)] focus:border-[var(--gf-blue)] outline-none transition-colors"
            />
          </div>
          
          <div>
            <label className="block text-sm text-[var(--gf-gray-text)] mb-2">Email</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-3 text-[var(--foreground)] focus:border-[var(--gf-blue)] outline-none transition-colors"
            />
          </div>
          
          <div>
            <label className="block text-sm text-[var(--gf-gray-text)] mb-2">Message</label>
            <textarea
              required
              rows={6}
              value={formData.message}
              onChange={(e) => setFormData({...formData, message: e.target.value})}
              className="w-full bg-[var(--gf-surface)] border border-[var(--gf-border)] rounded-xl p-3 text-[var(--foreground)] focus:border-[var(--gf-blue)] outline-none transition-colors resize-none"
            ></textarea>
          </div>
          
          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full bg-[var(--gf-blue)] text-black font-medium py-3 rounded-xl hover:bg-opacity-90 transition-colors disabled:opacity-50"
          >
            {status === "loading" ? "Sending..." : "Send Message"}
          </button>
          
          {status === "error" && (
            <p className="text-[var(--gf-red)] text-sm text-center">Failed to send message. Please try again later.</p>
          )}
        </form>
      )}
    </div>
  );
}
