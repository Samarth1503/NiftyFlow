"use client";

import { useAuth } from "@/context/AuthContext";
import { LogOut } from "lucide-react";

export default function LogoutButton() {
  const { user, logout } = useAuth();
  if (!user) return null;
  
  return (
    <button 
      onClick={logout} 
      className="flex items-center gap-2 text-sm text-[var(--gf-gray-text)] hover:text-white transition-colors"
    >
      <LogOut size={16} />
      Logout
    </button>
  );
}